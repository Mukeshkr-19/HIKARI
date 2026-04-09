#!/usr/bin/env python3
"""
HIKARI v2.0 - Main Entry Point
Smart hybrid: text-first with voice option
Push-to-talk voice mode (hold spacebar to speak)
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   ██╗  ██╗██╗  ██╗ ██████╗ ██╗    ██╗                    ║
║   ██║ ██╔╝██║  ██║██╔═══██╗██║    ██║                    ║
║   █████╔╝ ███████║██║   ██║██║ █╗ ██║                    ║
║   ██╔═██╗ ██╔══██║██║   ██║██║███╗██║                    ║
║   ██║  ██╗██║  ██║╚██████╔╝╚███╔███╔╝                    ║
║   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝  ╚══╝╚══╝                    ║
║                                                          ║
║              Personal AI Assistant v2.0                  ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)


def run_text_mode(orchestrator):
    """Text mode - reliable, always works"""
    print("\n" + "=" * 60)
    print("  HIKARI v2.0 - Text Mode")
    print("  Type your message and press Enter")
    print("  Type 'voice' to switch to voice mode")
    print("  Type 'exit' or 'goodbye' to quit")
    print("=" * 60 + "\n")

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() == "voice":
                run_voice_mode(orchestrator)
                return
            if user_input.lower() in ["exit", "quit", "goodbye", "bye"]:
                response = orchestrator._handle_exit()
                if response:
                    orchestrator.voice.speak(response)
                return
            response = orchestrator.process_input(user_input, source="text")
            if response:
                print(f"\nHIKARI: {response}")
                orchestrator.voice.speak(response)
        except KeyboardInterrupt:
            print("\nShutting down HIKARI...")
            break
        except EOFError:
            break


def run_voice_mode(orchestrator):
    """Voice mode with push-to-talk"""
    print("\n" + "=" * 60)
    print("  HIKARI v2.0 - Voice Mode")
    print("  Press ENTER to start listening, speak, then press ENTER again")
    print("  Or type 'text' to switch to text mode")
    print("  Type 'exit' or 'goodbye' to quit")
    print("=" * 60 + "\n")

    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good morning! I am HIKARI."
    elif hour < 17:
        greeting = "Good afternoon! I am HIKARI."
    else:
        greeting = "Good evening! I am HIKARI."

    print(f"HIKARI: {greeting}")
    orchestrator.voice.speak(greeting)

    while True:
        try:
            cmd = input("\n[Press ENTER to speak, or type command]: ").strip()

            if cmd.lower() in ["exit", "quit", "goodbye", "bye"]:
                response = orchestrator._handle_exit()
                orchestrator.voice.speak(response)
                return
            if cmd.lower() == "text":
                run_text_mode(orchestrator)
                return

            # Listen for speech
            print("[VOICE] Listening... (speak now)")
            user_input = orchestrator.voice.listen(timeout=10)

            if user_input:
                print(f"You: {user_input}")
                response = orchestrator.process_input(user_input, source="voice")
                if response:
                    print(f"\nHIKARI: {response}")
                    orchestrator.voice.speak(response)
            else:
                print("[VOICE] No speech detected. Try again.")

        except KeyboardInterrupt:
            print("\nShutting down HIKARI...")
            break
        except EOFError:
            break


def main():
    parser = argparse.ArgumentParser(description="HIKARI v2.0 - Personal AI Assistant")
    parser.add_argument("--text", action="store_true", help="Start in text mode")
    parser.add_argument("--voice", action="store_true", help="Start in voice mode")
    parser.add_argument(
        "--server", action="store_true", help="Run WebSocket server only"
    )
    parser.add_argument("--port", type=int, default=8765, help="WebSocket server port")
    parser.add_argument("--quiet", action="store_true", help="Suppress startup output")
    args = parser.parse_args()

    if not args.quiet:
        print_banner()

    from core.orchestrator import get_orchestrator

    orchestrator = get_orchestrator()

    # Start WebSocket server for phone connectivity
    orchestrator.start_server(port=args.port)
    conn_info = orchestrator.get_device_connection_info()
    print(f"\n📱 Phone: http://{conn_info['local_ip']}:{args.port}/connect")
    print(f"📷 QR: http://{conn_info['local_ip']}:{args.port}/qr")

    if args.server:
        print(f"\nServer running on port {args.port}. Ctrl+C to stop.")
        try:
            import time

            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    elif args.voice:
        run_voice_mode(orchestrator)
    else:
        run_text_mode(orchestrator)


if __name__ == "__main__":
    main()
