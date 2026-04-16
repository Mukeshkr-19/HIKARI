#!/usr/bin/env python3
"""HIKARI CLI — text banner, WebSocket UI, optional browser open."""

import os
import sys
import subprocess
import webbrowser

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


def _launch_voice_mode() -> None:
    """Hand off to hikari.py --voice (this CLI keeps the mic off)."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    py = os.path.join(repo_root, ".venv", "bin", "python")
    if not os.path.isfile(py):
        py = sys.executable
    script = os.path.join(repo_root, "src", "hikari.py")
    print("\n  → Voice mode: microphone ON. After the greeting, say “hikari” clearly.\n")
    print("  (This replaces the text CLI. Ctrl+C to stop.)\n")
    os.execv(py, [py, "-E", script, "--voice"])


def _open_url(url: str) -> None:
    """Open URL in default browser (macOS / Windows / Linux)."""
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", url], check=False)
        elif sys.platform.startswith("linux"):
            subprocess.run(["xdg-open", url], check=False)
        else:
            webbrowser.open(url)
    except Exception:
        webbrowser.open(url)


def main():
    port = int(os.environ.get("HIKARI_PORT", "8765"))
    os.environ.setdefault("HIKARI_QUIET", "1")

    os.system("clear" if os.name != "nt" else "cls")

    print("\n")
    print(HIKARI_BANNER)

    os.system(f"lsof -ti:{port} | xargs kill -9 2>/dev/null")

    import logging

    logging.disable(logging.CRITICAL)

    orchestrator = None
    try:
        from dotenv import load_dotenv

        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        load_dotenv()

        from core.orchestrator import get_orchestrator

        orchestrator = get_orchestrator(enable_mic=False)

        try:
            orchestrator.start_server(port=port)
        except OSError:
            pass
    except Exception as e:
        logging.disable(logging.NOTSET)
        print(f"\nCould not start HIKARI: {e}\n")
        sys.exit(1)
    finally:
        logging.disable(logging.NOTSET)

    if orchestrator is None:
        sys.exit(1)

    conn = orchestrator.get_device_connection_info()
    local_ip = conn.get("local_ip", "127.0.0.1")
    hud_local = f"http://127.0.0.1:{port}/hud"
    hud_lan = conn.get("hud_url", f"http://{local_ip}:{port}/hud")
    pairing = (
        getattr(orchestrator.ws_server, "pairing_code", None)
        if orchestrator.ws_server
        else None
    )

    print("=" * 50)
    print("  HIKARI is ready!")
    print("=" * 50)
    print("\n  Web UI (click or copy into browser):\n")
    print(f"    Local:   {hud_local}")
    print(f"    Network: {hud_lan}")
    if pairing:
        print(f"\n  Phone pairing code: {pairing}")
    print("\n  Type  ui    — open the HUD in your default browser")
    print("  Type  link  — show these URLs again")
    print("  Type  voice — wake-word + microphone (say “hikari”)")
    print("  Type  exit  — quit\n")
    print("  Note: This screen is text-only — the mic is off until you type  voice .\n")
    print("  Type your message below\n")

    if orchestrator.user_profile.needs_onboarding():
        print(f"HIKARI: {orchestrator.onboarding_intro_message()}\n")

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue

            lowered = user_input.lower()
            if lowered in ("exit", "quit", "bye", "goodbye"):
                print("\nGoodbye!")
                break
            if lowered in ("ui", "open", "hud", "browser"):
                print(f"Opening {hud_local} …")
                _open_url(hud_local)
                continue
            if lowered == "link":
                print(f"\n  Local:   {hud_local}\n  Network: {hud_lan}")
                if pairing:
                    print(f"  Pairing: {pairing}")
                print()
                continue
            if lowered in ("voice", "mic", "talk", "listen"):
                _launch_voice_mode()
                return

            if orchestrator.user_profile.needs_onboarding():
                ob = orchestrator.try_finish_onboarding(user_input)
                if ob:
                    print(f"\nHIKARI: {ob}\n")
                continue

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
