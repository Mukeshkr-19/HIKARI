# HIKARI v2.0 - Personal AI Assistant

> A multi-agent autonomous AI assistant with voice authentication, cross-device connectivity, and multi-provider AI routing.

## Features

- **Multi-Agent Swarm** - 6 specialized agents (Voice, Research, Files, System, Code, Memory) working autonomously
- **Multi-Provider AI Routing** - Smart routing across Google, Groq, OpenRouter, Cerebras, DeepSeek, NVIDIA, Cohere
- **Voice Authentication** - Voice print
- **Cross-Device** - Laptop as brain, phone/watch as interface via WebSocket
- **File System Access** - Secure, whitelisted file reading and searching
- **World Awareness** - Real-time news, weather, time, proactive alerts
- **Memory & Learning** - Persistent conversation history, user preferences, fact learning
- **Security First** - Encrypted API keys, file access policies, audit logging

## Quick Start

### 1. Install Dependencies

```bash
cd HIKARI
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Set Up API Keys

```bash
cp .env.example .env
# Edit .env and add your API keys (at least ONE AI provider required)
```

**Recommended minimum setup:**
- `GOOGLE_AI_STUDIO_KEY` - Best free tier (1M context window)
- `GROQ_API_KEY` - Fastest inference (300+ tokens/sec)

**Get free API keys:**
- Google AI Studio: https://aistudio.google.com
- Groq: https://console.groq.com
- OpenRouter: https://openrouter.ai
- Cerebras: https://cloud.cerebras.ai
- DeepSeek: https://platform.deepseek.com
- NVIDIA: https://build.nvidia.com

### 3. Run HIKARI

```bash
# Voice mode (default)
python3 hikari.py

# Text mode
python3 hikari.py --text

# Server only (for phone connections)
python3 hikari.py --server

# Custom port
python3 hikari.py --port 9000
```

## Connecting Your Phone

1. Start HIKARI on your laptop
2. Note the IP address and port shown in the terminal
3. On your phone, open: `http://<your-laptop-ip>:8765/hud` (hologram HUD) or `/connect`
4. Or scan the QR code: `http://<your-laptop-ip>:8765/qr`
5. Enter the 6-digit pairing code shown on your laptop

**Same WiFi network required.** Your laptop is the brain - phone is just an interface.

## Voice Activation

- **Wake Word**: Say "Hikari" to activate
- **Speaker lock (recommended)**: enroll your voice so only you can activate
- **Clap Detection**: Double-clap to activate (when enabled)
- **Codename**: optional fallback authentication (set your own in `.env`)

### Enroll your voice (speaker verification)

```bash
python src/hikari_daemon.py --enroll-voice
python src/hikari_daemon.py
```

## Commands

| Command | Description |
|---------|-------------|
| "What's the weather in [city]?" | Get weather info |
| "Open [app]" | Launch an application |
| "Open [website]" | Open a website |
| "What time is it?" | Current time |
| "What's the news?" | Latest headlines |
| "Morning briefing" | Full daily briefing |
| "Read my [file]" | Read a file (whitelisted dirs) |
| "Search for [query]" | Search files or web |
| "Remember that [fact]" | Store a fact |
| "What do you know about me?" | View stored memories |
| "Status" | System status report |
| "Exit" / "Goodbye" | Shut down |

## Architecture

```
hikari/
├── core/                    # Core systems
│   ├── orchestrator.py      # Agent swarm manager
│   ├── router.py            # Multi-provider AI routing
│   ├── voice.py             # Speech I/O, wake word, clap detection
│   └── memory.py            # Persistent memory system
├── agents/                  # Autonomous agents
│   ├── base.py              # Base agent class
│   ├── voice.py             # Voice authentication & I/O
│   ├── research.py          # Web search, news, weather
│   ├── files.py             # Secure file system access
│   ├── system.py            # Apps, websites, system info
│   ├── code.py              # Programming assistance
│   └── memory_agent.py      # Memory & personalization
├── security/                # Security layer
│   └── auth.py              # Voice print, codename, policies
├── skills/                  # Extensible skills
├── config/                  # Configuration files
├── data/                    # Runtime data (memory, voice prints)
├── hikari-frontend/         # Next.js PWA (optional)
├── src/server.py            # WebSocket + HTTP server
├── src/hikari.py            # Main entry point
├── requirements.txt         # Python dependencies
└── .env.example             # Environment template
```

## AI Provider Routing

HIKARI intelligently routes requests based on task type:

| Task Type | Provider | Model |
|-----------|----------|-------|
| Quick answers | Groq | Llama 3.3 70B |
| General chat | Google | Gemini 2.0 Flash |
| Deep reasoning | Google | Gemini 2.5 Pro |
| Coding | Groq | Qwen3 32B |
| Math | DeepSeek | DeepSeek Reasoner |
| Fallback | Cohere | Command R+ |

If a provider fails, HIKARI automatically falls back through the chain.

## Security

- All API keys stored in `.env` (never in code)
- File access restricted to whitelisted directories
- Voice prints stored locally, never sent to servers
- Codename hashed with SHA-256
- Agent action audit logging
- Pairing code for device connections

## Customization

### Add a new agent

```python
# agents/my_agent.py
from agents.base import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__("my_agent", "Description")

    def handle(self, user_input: str, context: str = "") -> str:
        # Your logic here
        return "Response"

    def can_handle(self, user_input: str) -> float:
        # Return 0-1 confidence
        return 0.5
```

Then register in `core/orchestrator.py`:
```python
self.agents["my_agent"] = MyAgent()
```

### Add a new AI provider

Edit `core/router.py` and add to `PROVIDER_CONFIGS`.

## Troubleshooting

**No audio input:**
```bash
# macOS: Check microphone permissions in System Preferences > Security > Microphone
# Install PyAudio: brew install portaudio && pip install pyaudio
```

**WebSocket connection fails:**
- Ensure laptop and phone are on the same WiFi
- Check firewall settings allow port 8765
- Use `ifconfig` to find your laptop's IP address

**AI responses fail:**
- Check that at least one API key is set in `.env`
- Run `python3 hikari.py --text` to see detailed error logs
- Check provider status with "status" command

## License

MIT - Build something amazing.
