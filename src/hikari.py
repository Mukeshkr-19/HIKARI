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

os.environ.setdefault("HIKARI_QUIET", "1")


def _transcript_matches_wake(orchestrator, text: str) -> bool:
    """Whisper may output variants; match orchestrator wake_words plus light fuzzy checks."""
    if not text:
        return False
    t = text.lower().replace("'", "").replace("-", " ")
    for w in getattr(orchestrator, "wake_words", ()) or ["hikari"]:
        if w.lower() in t:
            return True
    compact = "".join(t.split())
    if "hikari" in compact or "shikari" in compact or "hickory" in compact:
        return True
    return False


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

    if orchestrator.user_profile.needs_onboarding():
        print(f"HIKARI: {orchestrator.onboarding_intro_message()}\n")

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
            if orchestrator.user_profile.needs_onboarding():
                ob = orchestrator.try_finish_onboarding(user_input)
                if ob:
                    print(f"\nHIKARI: {ob}\n")
                continue
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
    """Voice mode (wake-word gated, speaker-locked if enrolled)."""
    from core.quiet import is_quiet

    print("\n" + "=" * 60)
    print("  HIKARI v2.0 - Voice Mode")
    print("  Say 'hikari' (or 'shikari' / 'hickory') to wake — mic listens right after this greeting")
    print("  Say 'bye' / 'stop' / 'goodbye' to sleep again")
    print("  Later: Enter = listen again | type  text  |  exit")
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

    from core.speaker_auth import SpeakerAuth

    speaker = SpeakerAuth()
    speaker_warned = False

    def speaker_ok(audio) -> bool:
        if not speaker.is_enrolled():
            return True
        try:
            emb = speaker.embedding_from_speech_recognition_audio(audio)
            res = speaker.verify_embedding(emb)
            return bool(res.ok)
        except Exception:
            return False

    def listen_short_phrase() -> tuple[object, str | None]:
        nonlocal speaker_warned
        audio = orchestrator.voice.listen_audio(timeout=8, phrase_time_limit=5)
        if not audio:
            return None, None
        text = orchestrator.voice._recognize_with_whisper(audio)
        t = text.lower().strip() if text else None
        if not t:
            return audio, None
        # Transcribe before speaker check: short wake clips often fail ECAPA if verified first.
        if _transcript_matches_wake(orchestrator, t):
            if speaker.is_enrolled() and not speaker_ok(audio):
                if not speaker_warned:
                    print(
                        "\n[VOICE] Speaker lock: wake phrase did not match your enrolled voice.\n"
                        "  Re-enroll:  python src/hikari_daemon.py --enroll-voice\n"
                    )
                    speaker_warned = True
                return audio, None
        return audio, t

    voice_round = 0
    while True:
        try:
            voice_round += 1
            if voice_round > 1:
                cmd = input(
                    "\n[Enter = listen for wake word again | text | exit]: "
                ).strip().lower()
                if cmd in ("exit", "quit", "goodbye", "bye"):
                    response = orchestrator._handle_exit()
                    orchestrator.voice.speak(response)
                    return
                if cmd == "text":
                    run_text_mode(orchestrator)
                    return
                if cmd:
                    print(
                        "(Say 'hikari', or type  text  /  exit  to leave voice mode.)\n"
                    )

            print("\nSleep mode — say 'hikari' to wake me.\n")
            while True:
                _, text = listen_short_phrase()
                if not text:
                    continue
                if _transcript_matches_wake(orchestrator, text):
                    orchestrator.voice.speak("Yeah?")
                    break
                if not is_quiet():
                    print(f"[VOICE] Heard {text!r} — try a clearer 'hikari'.\n")

            while True:
                user_audio = orchestrator.voice.listen_audio(timeout=10, phrase_time_limit=20)
                if not user_audio:
                    continue
                if not speaker_ok(user_audio):
                    continue
                user_input = orchestrator.voice._recognize_with_whisper(user_audio)
                if not user_input:
                    continue
                lowered = user_input.lower().strip()
                print(f"You: {lowered}")
                if any(w in lowered for w in ["bye", "stop", "goodbye", "sleep"]):
                    orchestrator.voice.speak("Talk to you later!")
                    break
                response = orchestrator.process_input(lowered, source="voice")
                if response:
                    print(f"\nHIKARI: {response}")
                    orchestrator.voice.speak(response)

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
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show routing and provider logs (HIKARI_VERBOSE=1)",
    )
    args = parser.parse_args()

    if args.verbose:
        os.environ["HIKARI_VERBOSE"] = "1"

    if not args.quiet:
        print_banner()

    from core.orchestrator import get_orchestrator

    # Avoid microphone warmup unless explicitly running voice mode.
    # This prevents hangs on systems without mic permission / in server-only usage.
    orchestrator = get_orchestrator(enable_mic=bool(args.voice))

    # Start WebSocket server for phone connectivity
    orchestrator.start_server(port=args.port)
    conn_info = orchestrator.get_device_connection_info()
    print(f"\n📱 Phone HUD: http://{conn_info['local_ip']}:{args.port}/hud")
    print(f"📱 Connect: http://{conn_info['local_ip']}:{args.port}/connect")
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
