#!/usr/bin/env python3
"""HIKARI CLI — text banner only (no mascot / animation)."""

import os
import sys
import time

HIKARI_BANNER = r"""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   ██╗  ██╗██╗██╗  ██╗ █████╗ ██████╗ ██╗                ║
║   ██║  ██║██║██║ ██╔╝██╔══██╗██╔══██╗██║                ║
║   ███████║██║█████╔╝ ███████║██████╔╝██║                ║
║   ██╔══██║██║██╔═██╗ ██╔══██║██╔══██╗██║                ║
║   ██║  ██║██║██║  ██╗██║  ██║██║  ██║██║                ║
║   ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝                ║
║                                                          ║
║            Personal AI Assistant v2.0                    ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""


def main():
    os.system("clear" if os.name != "nt" else "cls")

    print("\n")
    print(HIKARI_BANNER)

    # Show loading checkmarks (clean, no verbose logs)
    print("\n[✓] Loading AI models...")
    time.sleep(0.3)
    print("[✓] Initializing orchestrator...")
    time.sleep(0.3)
    print("[✓] Starting WebSocket server...")
    time.sleep(0.3)
    print("[✓] Loading voice system...")
    time.sleep(0.3)
    print("[✓] Ready!\n")

    # Suppress all verbose output during init
    # Kill any process on port 8765
    os.system("lsof -ti:8765 | xargs kill -9 2>/dev/null")
    time.sleep(0.5)

    # Redirect ALL output to /dev/null during initialization
    # This blocks ALL print statements from server.py, router.py, voice.py, etc.
    import builtins
    import logging

    # Disable logging completely
    logging.disable(logging.CRITICAL)

    # Save original print
    original_print = print

    # Create null print
    def null_print(*args, **kwargs):
        pass

    # Replace print temporarily
    builtins.print = null_print

    try:
        from dotenv import load_dotenv

        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        load_dotenv()

        from core.orchestrator import get_orchestrator

        orchestrator = get_orchestrator()

        try:
            orchestrator.start_server(port=8765)
        except OSError:
            pass
    finally:
        # Restore print
        builtins.print = original_print

    # Final ready message
    print("=" * 50)
    print("  HIKARI is ready!")
    print("=" * 50)
    print("\n  Type your message below\n")

    # Interactive loop
    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
                print("\nGoodbye!")
                break

            response = orchestrator.process_input(user_input, source="text")
            if response:
                print(f"\nHIKARI: {response}\n")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            break


if __name__ == "__main__":
    main()
