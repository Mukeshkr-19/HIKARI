#!/usr/bin/env python3
"""
HIKARI v3 - Main Entry Point

Usage:
    python3 hikari.py                 # Interactive text mode
    python3 hikari.py --daemon        # Always listening (no wake word needed)
    python3 hikari.py --tray          # System tray icon mode
    python3 hikari.py --install       # Install as login item (starts on boot)
    python3 hikari.py --install-cli   # Install hikari/Hikari shell commands
"""

import os
import sys
import re
import argparse
import subprocess
from textwrap import dedent

# Hide dock icon when running as service
if "--daemon" in sys.argv or "--bg" in sys.argv or "--tray" in sys.argv:
    try:
        from AppKit import NSApplication
        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(2)
    except:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["OBJC_DISABLE_INITIALIZE_BRIDGE"] = "1"

def print_banner():
    banner = dedent(
        """
        +------------------------------------------------------------+
        |                                                            |
        |   _   _ ___ _  __    _    ____  ___                       |
        |  | | | |_ _| |/ /   / \\  |  _ \\|_ _|                      |
        |  | |_| || || ' /   / _ \\ | |_) || |                       |
        |  |  _  || || . \\  / ___ \\|  _ < | |                       |
        |  |_| |_|___|_|\\_\\/_/   \\_\\_| \\_\\___|                      |
        |                                                            |
        |          Your 24/7 AI Assistant - Always Listening         |
        |                                                            |
        +------------------------------------------------------------+
        """
    ).strip("\n")

    print(f"{banner}\n")

def run_daemon():
    """Run as always-listening service (no wake word needed)"""
    print("[*] Starting HIKARI in background mode...")
    print("[*] Just speak and I'll respond - no wake word needed!")
    print("[*] Say 'exit' to stop listening\n")

    from services.hikari_service import HIKARI_Daemon
    HIKARI_Daemon().run()

def run_tray():
    """Run as system tray icon"""
    print("[*] Starting HIKARI in system tray mode...")
    print("[*] Look for icon in menu bar\n")

    try:
        import rumps
        from services.hikari_tray import HIKARI_Tray
        HIKARI_Tray().run()
    except ImportError:
        print("[!] rumps not installed. Install with: pip install rumps")
        print("[*] Or run --daemon instead")

def run_server(host: str, port: int):
    """Run the WebSocket/HTTP server for phone and web clients"""
    print_banner()
    print(f"[*] Starting HIKARI server on {host}:{port}...")

    from core.orchestrator import get_orchestrator
    from core.server import WebSocketServer

    orchestrator = get_orchestrator()
    WebSocketServer(orchestrator, host=host, port=port).start()

def run_interactive():
    """Run in interactive text mode"""
    print_banner()

    from core.orchestrator import get_orchestrator

    orchestrator = get_orchestrator()

    print("Ready. Type a message, or 'exit' to quit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "bye"]:
                print("\nHIKARI: Goodbye.")
                break

            response = orchestrator.process_input(user_input, source="text")
            if response:
                print(f"\nHIKARI: {response}\n")

        except KeyboardInterrupt:
            print("\nHIKARI: Shutting down.")
            break
        except EOFError:
            break

def install_service():
    """Install HIKARI as login item (runs on Mac startup)"""
    python_path = subprocess.run(["which", "python3"], capture_output=True, text=True).stdout.strip()

    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.hikari.ai</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>{os.path.abspath(__file__)}</string>
        <string>--daemon</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>"""

    plist_path = os.path.expanduser("~/Library/LaunchAgents/com.hikari.ai.plist")
    os.makedirs(os.path.dirname(plist_path), exist_ok=True)

    with open(plist_path, "w") as f:
        f.write(plist)

    subprocess.run(["launchctl", "load", plist_path])
    print("[+] HIKARI installed as login item!")
    print("[+] Restart your Mac to start HIKARI automatically.")

def run_repo_script(script_name: str):
    """Run a repo-local script."""
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts", script_name)
    raise SystemExit(subprocess.run(["bash", script_path]).returncode)

def main():
    parser = argparse.ArgumentParser(
        description="HIKARI personal AI assistant",
    )
    parser.add_argument(
        "--text",
        action="store_true",
        help="Run interactive text mode. This is the default.",
    )
    parser.add_argument(
        "--daemon",
        "--bg",
        dest="daemon",
        action="store_true",
        help="Run always-listening background mode.",
    )
    parser.add_argument(
        "--tray",
        action="store_true",
        help="Run HIKARI from the macOS menu bar.",
    )
    parser.add_argument(
        "--server",
        action="store_true",
        help="Run the WebSocket/HTTP server for phone and web clients.",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for --server mode. Default: 0.0.0.0.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port for --server mode. Default: 8765.",
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install HIKARI as a macOS login item.",
    )
    parser.add_argument(
        "--install-cli",
        action="store_true",
        help="Install hikari/Hikari shell commands into a PATH directory.",
    )
    parser.add_argument(
        "--uninstall-cli",
        action="store_true",
        help="Remove hikari/Hikari shell commands installed for this repo.",
    )
    parser.add_argument(
        "--doctor",
        action="store_true",
        help="Run a quick HIKARI workspace health/status check.",
    )
    parser.add_argument(
        "--doctor-full",
        action="store_true",
        help="Run doctor plus CLI, text, test, lint, and build checks.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show internal initialization, routing, scheduler, and memory logs.",
    )

    args = parser.parse_args()

    if args.verbose:
        os.environ["HIKARI_VERBOSE"] = "1"
        os.environ["HIKARI_QUIET"] = "0"

    if args.doctor or args.doctor_full:
        from core.doctor import run_doctor

        raise SystemExit(run_doctor(full=args.doctor_full))

    if args.install:
        install_service()
        return

    if args.install_cli:
        run_repo_script("install-hikari-cli.sh")

    if args.uninstall_cli:
        run_repo_script("uninstall-hikari-cli.sh")

    if args.tray:
        run_tray()
        return

    if args.server:
        run_server(args.host, args.port)
        return

    if args.daemon:
        run_daemon()
        return

    run_interactive()

if __name__ == "__main__":
    main()
