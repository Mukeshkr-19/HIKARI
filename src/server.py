"""
HIKARI v2.0 - WebSocket Server
Enables phone/watch/AirPods connectivity via WebSocket + HTTP
QR code generation for easy phone pairing
"""

import os
import sys
import json
import time
import asyncio
import threading
import hashlib
from typing import Optional, Dict, Any, Set
from datetime import datetime
from http import HTTPStatus

from core.quiet import is_quiet

try:
    import websockets
    from websockets.server import serve

    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

try:
    import qrcode
    import io
    import base64

    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False


class WebSocketServer:
    """WebSocket server for device connections"""

    def __init__(self, orchestrator, host: str = "0.0.0.0", port: int = 8765):
        self.orchestrator = orchestrator
        self.host = host
        self.port = port
        self.connected_clients: Set = set()
        self.device_info: Dict[str, Dict] = {}
        self._server = None
        self._running = False
        self._loop = None
        self.pairing_code = self._generate_pairing_code()

    def _generate_pairing_code(self) -> str:
        """Generate a 6-digit pairing code"""
        return hashlib.md5(str(time.time()).encode()).hexdigest()[:6].upper()

    def start(self):
        """Start the WebSocket server"""
        if not WEBSOCKETS_AVAILABLE:
            print("[WS] websockets not installed, skipping server")
            return

        self._running = True
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        async def handler(websocket, path=None):
            await self._handle_connection(websocket)

        async def process_request(path, request_headers):
            """Handle HTTP requests for web interface and QR code"""
            if path == "/qr":
                return self._serve_qr_code()
            if path == "/connect":
                return self._serve_connect_page()
            if path == "/hud":
                return self._serve_hud_page()
            if path == "/api/status":
                return self._serve_api_status()
            return None  # Let WebSocket handle it

        start_server = serve(
            handler,
            self.host,
            self.port,
            process_request=process_request,
        )

        if not is_quiet():
            print(f"[WS] Server starting on {self.host}:{self.port}")
            print(f"[WS] Pairing code: {self.pairing_code}")
            print(f"[WS] Connect from phone: http://<your-ip>:{self.port}/connect")

        self._loop.run_until_complete(start_server)
        self._loop.run_forever()

    async def _handle_connection(self, websocket):
        """Handle a new WebSocket connection"""
        client_id = id(websocket)
        self.connected_clients.add(websocket)

        # Send welcome message
        await websocket.send(
            json.dumps(
                {
                    "type": "welcome",
                    "pairing_code": self.pairing_code,
                    "message": "Connected to HIKARI",
                    "devices": len(self.connected_clients),
                }
            )
        )

        self.device_info[str(client_id)] = {
            "connected_at": datetime.now().isoformat(),
            "type": "unknown",
        }

        if not is_quiet():
            print(f"[WS] Client connected ({len(self.connected_clients)} total)")

        try:
            async for message in websocket:
                await self._handle_message(websocket, message)
        except Exception as e:
            print(f"[WS] Client error: {e}")
        finally:
            self.connected_clients.discard(websocket)
            if not is_quiet():
                print(f"[WS] Client disconnected ({len(self.connected_clients)} total)")

    async def _handle_message(self, websocket, message: str):
        """Process incoming message from client"""
        try:
            data = json.loads(message)
            msg_type = data.get("type", "")

            if msg_type == "identify":
                device_type = data.get("device_type", "unknown")
                client_id = str(id(websocket))
                self.device_info[client_id]["type"] = device_type
                await websocket.send(
                    json.dumps(
                        {
                            "type": "identified",
                            "device_type": device_type,
                        }
                    )
                )

            elif msg_type == "pair":
                code = data.get("code", "")
                if code == self.pairing_code:
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "paired",
                                "message": "Device paired successfully",
                            }
                        )
                    )
                else:
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "pair_error",
                                "message": "Invalid pairing code",
                            }
                        )
                    )

            elif msg_type == "message":
                # Process user message through orchestrator (thread + timeout so WS loop stays responsive)
                user_input = data.get("text", "")
                if user_input:
                    try:
                        response = await asyncio.wait_for(
                            asyncio.to_thread(
                                self.orchestrator.process_input,
                                user_input,
                                "device",
                            ),
                            timeout=240.0,
                        )
                    except asyncio.TimeoutError:
                        await websocket.send(
                            json.dumps(
                                {
                                    "type": "error",
                                    "message": "Request timed out (over 4 minutes). Check API keys / network on the Mac.",
                                }
                            )
                        )
                    else:
                        await websocket.send(
                            json.dumps(
                                {
                                    "type": "response",
                                    "text": response or "No response generated",
                                }
                            )
                        )

            elif msg_type == "voice":
                # Handle voice data from device
                audio_data = data.get("audio", "")
                text = data.get("text", "")
                if text:
                    try:
                        response = await asyncio.wait_for(
                            asyncio.to_thread(
                                self.orchestrator.process_input,
                                text,
                                "voice_remote",
                            ),
                            timeout=240.0,
                        )
                    except asyncio.TimeoutError:
                        await websocket.send(
                            json.dumps(
                                {
                                    "type": "error",
                                    "message": "Voice request timed out. Check the Mac terminal for router/API errors.",
                                }
                            )
                        )
                    else:
                        await websocket.send(
                            json.dumps(
                                {
                                    "type": "response",
                                    "text": response or "",
                                }
                            )
                        )

            elif msg_type == "status":
                status = self.orchestrator._get_status_report()
                await websocket.send(
                    json.dumps(
                        {
                            "type": "status",
                            "text": status,
                        }
                    )
                )

            elif msg_type == "ping":
                await websocket.send(json.dumps({"type": "pong"}))

        except json.JSONDecodeError:
            await websocket.send(
                json.dumps(
                    {
                        "type": "error",
                        "message": "Invalid JSON",
                    }
                )
            )
        except Exception as e:
            await websocket.send(
                json.dumps(
                    {
                        "type": "error",
                        "message": str(e),
                    }
                )
            )

    def broadcast(self, message: Dict):
        """Send message to all connected clients"""
        data = json.dumps(message)
        for client in self.connected_clients.copy():
            try:
                asyncio.run_coroutine_threadsafe(
                    client.send(data),
                    self._loop,
                )
            except Exception:
                pass

    def _serve_qr_code(self):
        """Serve QR code image"""
        if not QR_AVAILABLE:
            return None

        import socket

        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        url = f"http://{local_ip}:{self.port}/connect"

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        img_base64 = base64.b64encode(buffer.read()).decode()

        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>HIKARI - QR Code</title></head>
        <body style="background:#0a0a0a;color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;font-family:system-ui;">
            <h1>Scan to connect</h1>
            <img src="data:image/png;base64,{img_base64}" alt="QR Code" />
            <p style="margin-top:20px;">Pairing code: <strong>{self.pairing_code}</strong></p>
            <p>Or open: <code>{url}</code></p>
        </body>
        </html>
        """
        return HTTPStatus.OK, [("Content-Type", "text/html")], html.encode()

    def _serve_connect_page(self):
        """Serve the connection page for phones"""
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <meta name="apple-mobile-web-app-capable" content="yes">
            <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
            <meta name="theme-color" content="#0a0a0a">
            <title>HIKARI</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { background: #0a0a0a; color: #e0e0e0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; height: 100vh; display: flex; flex-direction: column; }
                .header { padding: 20px; text-align: center; border-bottom: 1px solid #222; }
                .header h1 { font-size: 24px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
                .status { font-size: 12px; color: #666; margin-top: 5px; }
                .status.connected { color: #4ade80; }
                .chat { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 12px; }
                .message { max-width: 85%; padding: 12px 16px; border-radius: 18px; font-size: 15px; line-height: 1.4; }
                .message.user { align-self: flex-end; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-bottom-right-radius: 4px; }
                .message.ai { align-self: flex-start; background: #1a1a2e; border: 1px solid #333; border-bottom-left-radius: 4px; }
                .input-area { padding: 15px; border-top: 1px solid #222; display: flex; gap: 10px; }
                .input-area input { flex: 1; background: #1a1a2e; border: 1px solid #333; border-radius: 25px; padding: 12px 20px; color: white; font-size: 16px; outline: none; }
                .input-area input:focus { border-color: #667eea; }
                .input-area button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; border-radius: 25px; padding: 12px 24px; color: white; font-size: 16px; cursor: pointer; }
                .pairing { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; padding: 20px; }
                .pairing input { background: #1a1a2e; border: 1px solid #333; border-radius: 12px; padding: 15px; color: white; font-size: 24px; text-align: center; width: 200px; letter-spacing: 8px; margin: 20px 0; }
                .pairing button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; border-radius: 12px; padding: 15px 40px; color: white; font-size: 16px; cursor: pointer; }
                .hidden { display: none !important; }
                .orb { width: 60px; height: 60px; border-radius: 50%; background: radial-gradient(circle, #667eea, #764ba2); margin: 0 auto 20px; animation: pulse 2s infinite; }
                @keyframes pulse { 0%, 100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.1); opacity: 0.8; } }
                .typing { color: #666; font-size: 14px; padding: 8px 16px; align-self: flex-start; }
            </style>
        </head>
        <body>
            <div id="pairing-screen" class="pairing">
                <div class="orb"></div>
                <h2>Connect to HIKARI</h2>
                <p style="color:#666;margin-top:10px;">Enter the pairing code shown on your computer</p>
                <input type="text" id="pairing-code" placeholder="000000" maxlength="6" autocomplete="off">
                <button onclick="pair()">Connect</button>
            </div>

            <div id="chat-screen" class="hidden" style="height:100%;display:flex;flex-direction:column;">
                <div class="header">
                    <h1>HIKARI</h1>
                    <div id="connection-status" class="status">Connecting...</div>
                </div>
                <div id="chat-messages" class="chat"></div>
                <div class="input-area">
                    <input type="text" id="message-input" placeholder="Ask me anything..." autocomplete="off">
                    <button onclick="sendMessage()">Send</button>
                </div>
            </div>

            <script>
                let ws = null;
                const pairingCode = document.getElementById('pairing-code');
                const pairingScreen = document.getElementById('pairing-screen');
                const chatScreen = document.getElementById('chat-screen');
                const chatMessages = document.getElementById('chat-messages');
                const messageInput = document.getElementById('message-input');
                const statusEl = document.getElementById('connection-status');

                function connect() {
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    ws = new WebSocket(protocol + '//' + window.location.host);

                    ws.onopen = () => {
                        statusEl.textContent = 'Connected';
                        statusEl.classList.add('connected');
                    };

                    ws.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        if (data.type === 'response') {
                            addMessage(data.text, 'ai');
                        }
                    };

                    ws.onclose = () => {
                        statusEl.textContent = 'Disconnected - reconnecting...';
                        statusEl.classList.remove('connected');
                        setTimeout(connect, 3000);
                    };
                }

                function pair() {
                    const code = pairingCode.value.trim();
                    if (code.length !== 6) return;

                    connect();
                    ws.onopen = () => {
                        ws.send(JSON.stringify({
                            type: 'pair',
                            code: code,
                            device_type: 'mobile'
                        }));
                    };

                    ws.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        if (data.type === 'paired') {
                            pairingScreen.classList.add('hidden');
                            chatScreen.classList.remove('hidden');
                            chatScreen.style.display = 'flex';
                            statusEl.textContent = 'Connected';
                            statusEl.classList.add('connected');
                            addMessage('Connected! Ask me anything.', 'ai');
                        } else if (data.type === 'pair_error') {
                            alert('Invalid pairing code. Try again.');
                        } else if (data.type === 'response') {
                            addMessage(data.text, 'ai');
                        }
                    };
                }

                function sendMessage() {
                    const text = messageInput.value.trim();
                    if (!text || !ws) return;

                    addMessage(text, 'user');
                    ws.send(JSON.stringify({ type: 'message', text: text }));
                    messageInput.value = '';
                }

                function addMessage(text, type) {
                    const div = document.createElement('div');
                    div.className = 'message ' + type;
                    div.textContent = text;
                    chatMessages.appendChild(div);
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }

                messageInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') sendMessage();
                });

                pairingCode.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') pair();
                });
            </script>
        </body>
        </html>
        """
        return HTTPStatus.OK, [("Content-Type", "text/html")], html.encode()

    def _serve_hud_page(self):
        """Full-screen hologram-style HUD (phone + desktop). Same WebSocket protocol as /connect."""
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <meta name="theme-color" content="#0a1628">
            <title>HIKARI</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    background: #040814;
                    color: #e8f4ff;
                    font-family: ui-sans-serif, system-ui, -apple-system, sans-serif;
                    min-height: 100vh;
                    overflow-x: hidden;
                }
                /* Full-screen art: new random landscape on each HUD load (Unsplash — scenic / painterly). */
                #hud-bg-scene {
                    position: fixed;
                    inset: 0;
                    z-index: 0;
                    background-color: #0a1628;
                    background-size: cover;
                    background-position: center;
                    background-repeat: no-repeat;
                    pointer-events: none;
                }
                .hud-wrap { position: relative; z-index: 1; display: flex; flex-direction: column; min-height: 100vh; }
                .hud-header { text-align: center; padding: 1rem; border-bottom: 1px solid rgba(0,255,255,0.12); background: rgba(2,8,20,0.35); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); }
                .hud-header h1 {
                    font-size: 1.1rem; letter-spacing: 0.4em; font-weight: 300;
                    color: rgba(180,230,255,0.9); text-transform: uppercase;
                }
                .hud-core {
                    flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;
                    padding: 1rem; position: relative;
                }
                .holo-stack { position: relative; width: min(72vw, 280px); height: min(72vw, 280px); animation: stack-drift 14s ease-in-out infinite; }
                .ring {
                    position: absolute; inset: 0; border-radius: 50%;
                    border: 2px solid rgba(0,255,255,0.15);
                    animation: spin 12s linear infinite;
                }
                .ring.r2 { inset: 6%; border-color: rgba(100,200,255,0.2); animation-duration: 18s; animation-direction: reverse; }
                .ring.r3 { inset: 12%; border-color: rgba(0,200,255,0.12); animation-duration: 9s; }
                .core {
                    position: absolute; inset: 22%; border-radius: 50%;
                    background: radial-gradient(circle at 35% 30%, rgba(180,255,255,0.35), rgba(0,120,200,0.15) 40%, transparent 70%);
                    box-shadow: 0 0 60px rgba(0,200,255,0.35), inset 0 0 40px rgba(255,255,255,0.08);
                    transition: transform 0.4s ease, box-shadow 0.4s ease;
                }
                .core.idle { animation: breeze 9s ease-in-out infinite; }
                .core.speaking { animation: none; transform: scale(1.08); box-shadow: 0 0 80px rgba(0,255,200,0.5); }
                .core.thinking { animation: breathe 0.85s ease-in-out infinite; }
                @keyframes spin { to { transform: rotate(360deg); } }
                @keyframes stack-drift {
                    0%, 100% { transform: translate(0, 0) rotate(0deg); }
                    33% { transform: translate(3px, -4px) rotate(0.8deg); }
                    66% { transform: translate(-3px, 2px) rotate(-0.6deg); }
                }
                @keyframes breeze {
                    0%, 100% { transform: translate(0, 0) scale(1); filter: brightness(1); }
                    20% { transform: translate(2px, -2px) scale(1.02); filter: brightness(1.05); }
                    45% { transform: translate(-2px, 1px) scale(1); filter: brightness(1.02); }
                    70% { transform: translate(1px, 2px) scale(1.015); filter: brightness(1.04); }
                }
                @keyframes breathe { 0%,100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.05); opacity: 0.9; } }
                .state-label { margin-top: 1.5rem; font-size: 0.75rem; letter-spacing: 0.25em; color: rgba(150,220,255,0.55); text-transform: uppercase; }
                .pairing { display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; padding: 1.5rem; }
                .pairing input {
                    background: rgba(0,40,80,0.4); border: 1px solid rgba(0,255,255,0.25);
                    border-radius: 12px; padding: 14px; color: #fff; font-size: 1.4rem; text-align: center;
                    width: 200px; letter-spacing: 0.4em; margin: 1rem 0;
                }
                .pairing button, .input-area button {
                    background: linear-gradient(135deg, rgba(0,200,255,0.35), rgba(100,100,255,0.35));
                    border: 1px solid rgba(0,255,255,0.35); border-radius: 12px; padding: 14px 36px; color: #fff;
                    font-size: 1rem; cursor: pointer;
                }
                .chat { flex: 1; overflow-y: auto; padding: 1rem; display: flex; flex-direction: column; gap: 10px; max-height: 40vh; }
                .message { max-width: 90%; padding: 10px 14px; border-radius: 14px; font-size: 0.95rem; line-height: 1.45; backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); }
                .message.user { align-self: flex-end; background: rgba(0,120,200,0.42); border: 1px solid rgba(0,255,255,0.28); }
                .message.ai { align-self: flex-start; background: rgba(0,30,60,0.58); border: 1px solid rgba(0,200,255,0.22); }
                .input-area { padding: 1rem; border-top: 1px solid rgba(0,255,255,0.1); display: flex; gap: 10px; background: rgba(2,8,20,0.4); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); }
                .input-area input { flex: 1; background: rgba(0,40,80,0.35); border: 1px solid rgba(0,255,255,0.2); border-radius: 12px; padding: 12px 16px; color: #fff; font-size: 1rem; }
                .hidden { display: none !important; }
                .status { font-size: 0.75rem; color: rgba(150,200,255,0.5); margin-top: 0.25rem; }
                .status.ok { color: #4ade80; }
            </style>
        </head>
        <body>
            <div id="hud-bg-scene" aria-hidden="true"></div>
            <div class="hud-wrap">
                <div class="hud-header"><h1>HIKARI</h1><div id="st" class="status">Offline</div></div>"""
        html += """
                <div id="pairing-screen" class="pairing">
                    <div class="holo-stack">
                        <div class="ring"></div><div class="ring r2"></div><div class="ring r3"></div>
                        <div id="core" class="core idle"></div>
                    </div>
                    <p class="state-label">Enter pairing code</p>
                    <input type="text" id="pairing-code" placeholder="000000" maxlength="6" autocomplete="off">
                    <button onclick="pair()">Connect</button>
                </div>
                <div id="chat-screen" class="hidden" style="height:100%;display:flex;flex-direction:column;">
                    <div class="hud-core">
                        <div class="holo-stack">
                            <div class="ring"></div><div class="ring r2"></div><div class="ring r3"></div>
                            <div id="core2" class="core idle"></div>
                        </div>
                        <p id="lbl" class="state-label">Ready</p>
                    </div>
                    <div id="chat-messages" class="chat"></div>
                    <div class="input-area">
                        <input type="text" id="message-input" placeholder="Command HIKARI..." autocomplete="off">
                        <button onclick="sendMessage()">Send</button>
                    </div>
                </div>
            </div>
            <script>
                (function pickHudBackground() {
                    var ov = 'linear-gradient(180deg, rgba(4,10,24,0.82) 0%, rgba(8,20,40,0.55) 45%, rgba(2,6,16,0.92) 100%)';
                    var urls = [
                        'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?auto=format&fit=crop&w=1920&q=80',
                        'https://images.unsplash.com/photo-1469474968028-56623f2e60e4?auto=format&fit=crop&w=1920&q=80',
                        'https://images.unsplash.com/photo-1472214103451-9374bd1c798e?auto=format&fit=crop&w=1920&q=80',
                        'https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=1920&q=80',
                        'https://images.unsplash.com/photo-1433086966358-54859d0ed716?auto=format&fit=crop&w=1920&q=80',
                        'https://images.unsplash.com/photo-1490806843957-31f4c9a91c65?auto=format&fit=crop&w=1920&q=80',
                        'https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=1920&q=80',
                        'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1920&q=80',
                        'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1920&q=80',
                        'https://images.unsplash.com/photo-1519904981063-b0cf448d479e?auto=format&fit=crop&w=1920&q=80',
                        'https://images.unsplash.com/photo-1523712999610-f77fbcfc3843?auto=format&fit=crop&w=1920&q=80',
                        'https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=1920&q=80'
                    ];
                    var u = urls[Math.floor(Math.random() * urls.length)];
                    var el = document.getElementById('hud-bg-scene');
                    if (el) el.style.backgroundImage = ov + ', url(' + u + ')';
                })();

                let ws = null;
                let replyTimer = null;
                const pairingCode = document.getElementById('pairing-code');
                const pairingScreen = document.getElementById('pairing-screen');
                const chatScreen = document.getElementById('chat-screen');
                const chatMessages = document.getElementById('chat-messages');
                const messageInput = document.getElementById('message-input');
                const st = document.getElementById('st');
                const core2 = document.getElementById('core2');
                const lbl = document.getElementById('lbl');

                function clearReplyTimer() {
                    if (replyTimer) { clearTimeout(replyTimer); replyTimer = null; }
                }

                function setOrb(mode) {
                    core2.classList.remove('idle', 'thinking', 'speaking');
                    if (mode === 'idle') core2.classList.add('idle');
                    if (mode === 'thinking') core2.classList.add('thinking');
                    if (mode === 'speaking') core2.classList.add('speaking');
                }

                function resetAfterSend() {
                    clearReplyTimer();
                    setOrb('idle');
                    lbl.textContent = 'Ready';
                }

                function pair() {
                    const code = pairingCode.value.trim();
                    if (code.length !== 6) return;
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    ws = new WebSocket(protocol + '//' + window.location.host);
                    ws.onopen = () => {
                        ws.send(JSON.stringify({ type: 'pair', code: code, device_type: 'mobile' }));
                    };
                    ws.onmessage = (event) => {
                        let data;
                        try { data = JSON.parse(event.data); } catch (e) {
                            addMessage('Bad message from server.', 'ai');
                            resetAfterSend();
                            return;
                        }
                        if (data.type === 'welcome') return;
                        if (data.type === 'paired') {
                            pairingScreen.classList.add('hidden');
                            chatScreen.classList.remove('hidden');
                            chatScreen.style.display = 'flex';
                            st.textContent = 'Linked';
                            st.classList.add('ok');
                            lbl.textContent = 'Ready';
                            setOrb('idle');
                            addMessage('Connected. Your Mac runs HIKARI — commands execute there.', 'ai');
                        } else if (data.type === 'pair_error') {
                            alert('Invalid pairing code.');
                        } else if (data.type === 'error') {
                            clearReplyTimer();
                            setOrb('idle');
                            lbl.textContent = 'Error';
                            addMessage('Error: ' + (data.message || 'unknown'), 'ai');
                        } else if (data.type === 'response') {
                            clearReplyTimer();
                            setOrb('speaking');
                            lbl.textContent = 'Speaking';
                            addMessage(data.text, 'ai');
                            setTimeout(() => { setOrb('idle'); lbl.textContent = 'Ready'; }, 1500);
                        }
                    };
                    ws.onerror = () => {
                        st.textContent = 'Connection error';
                        st.classList.remove('ok');
                        resetAfterSend();
                    };
                    ws.onclose = () => { st.textContent = 'Disconnected'; st.classList.remove('ok'); clearReplyTimer(); setOrb('idle'); };
                }

                function sendMessage() {
                    const text = messageInput.value.trim();
                    if (!text || !ws) return;
                    if (ws.readyState !== WebSocket.OPEN) {
                        addMessage('Not connected. Refresh and pair again.', 'ai');
                        return;
                    }
                    clearReplyTimer();
                    setOrb('thinking');
                    lbl.textContent = 'Sending';
                    addMessage(text, 'user');
                    ws.send(JSON.stringify({ type: 'message', text: text }));
                    messageInput.value = '';
                    replyTimer = setTimeout(() => {
                        setOrb('idle');
                        lbl.textContent = 'Timed out';
                        addMessage('No reply yet (4+ min). Check the Mac running HIKARI — terminal errors or API keys.', 'ai');
                        replyTimer = null;
                    }, 250000);
                }

                function addMessage(text, type) {
                    const div = document.createElement('div');
                    div.className = 'message ' + type;
                    div.textContent = text;
                    chatMessages.appendChild(div);
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }

                messageInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMessage(); });
                pairingCode.addEventListener('keypress', (e) => { if (e.key === 'Enter') pair(); });
            </script>
        </body>
        </html>
        """
        return HTTPStatus.OK, [("Content-Type", "text/html")], html.encode()

    def _serve_api_status(self):
        """Serve API status as JSON"""
        status = {
            "running": self._running,
            "clients": len(self.connected_clients),
            "pairing_code": self.pairing_code,
            "devices": self.device_info,
        }
        return (
            HTTPStatus.OK,
            [("Content-Type", "application/json")],
            json.dumps(status).encode(),
        )

    def stop(self):
        """Stop the server"""
        self._running = False
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        print("[WS] Server stopped")
