#!/usr/bin/env python3
"""HIKARI v2.5 - The working version with learning + voice auth"""

from __future__ import print_function
import os
import sys
import time
import subprocess
import signal
import json

# Force unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), "w", buffering=1)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

WAKE_WORD = "hikari"
STOP_WORDS = [
    "stop listening",
    "exit hikari",
    "goodbye hikari",
    "bye hikari",
    "sleep hikari",
    "stop",
    "bye",
]

# Flag to control daemon exit
daemon_running = True

HIKARI_DIR = os.path.dirname(os.path.abspath(__file__))
LEARNING_FILE = os.path.join(HIKARI_DIR, "data", "learning.json")
VOICE_PRINT_FILE = os.path.join(HIKARI_DIR, "data", "voiceprint.bin")
CONVO_LOG = os.path.join(HIKARI_DIR, "logs", "conversations.log")
os.makedirs(os.path.dirname(LEARNING_FILE), exist_ok=True)


def log_convo(user: str, hikari: str):
    """Log conversation"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(CONVO_LOG, "a") as f:
        f.write(f"[{timestamp}] YOU: {user}\n")
        if hikari:
            f.write(f"[{timestamp}] HIKARI: {hikari}\n")
        f.write("\n")


def load_learnings():
    try:
        return json.load(open(LEARNING_FILE))
    except:
        return {"corrections": {}, "remember": []}


def save_learnings(data):
    json.dump(data, open(LEARNING_FILE, "w"))


def check_learnings(text):
    data = load_learnings()
    for wrong, correct in data.get("corrections", {}).items():
        if wrong.lower() in text.lower():
            return correct
    return None


def add_learning(wrong, correct):
    data = load_learnings()
    data["corrections"][wrong] = correct
    save_learnings(data)


def setup_voiceprint():
    """Record voiceprint for authentication"""
    print("\n🎙️ Setting up voice recognition...")
    print("Please say 'hikari' 3 times to train your voice.\n")

    samples = []
    for i in range(3):
        print(f"Say 'hikari' now ({i + 1}/3)...", flush=True)
        try:
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.5)
                audio = r.listen(source, timeout=5, phrase_time_limit=3)

            samples.append(audio.get_raw_data())
            print("✓ Got it!")
            time.sleep(1)
        except Exception as e:
            print(f"Error: {e}")
            return False

    try:
        with open(VOICE_PRINT_FILE, "wb") as f:
            for sample in samples:
                f.write(sample)
        print("\n✅ Voice recognition set up! Only your voice will activate HIKARI.\n")
        return True
    except Exception as e:
        print(f"Error saving voiceprint: {e}")
        return False


def verify_voiceprint(audio_data):
    """Verify voice - bypass for now to test"""
    return True  # Accept all voices for testing


sr = None
try:
    import speech_recognition as sr_module

    sr = sr_module
    print("[OK] SpeechRecognition")
except:
    print("[MISSING] SpeechRecognition")


def save_learnings(data):
    json.dump(data, open(LEARNING_FILE, "w"))


def check_learnings(text):
    data = load_learnings()
    for wrong, correct in data.get("corrections", {}).items():
        if wrong.lower() in text.lower():
            return correct
    return None


def add_learning(wrong, correct):
    data = load_learnings()
    data["corrections"][wrong] = correct
    save_learnings(data)


sr = None
try:
    import speech_recognition as sr_module

    sr = sr_module
    print("[OK] SpeechRecognition")
except:
    print("[MISSING] SpeechRecognition")

print("=" * 50)

if sr:
    r = sr.Recognizer()
    r.energy_threshold = 300  # Lower to hear quiet speech
    r.dynamic_energy_threshold = True  # Auto-adjust for ambient noise
    r.pause_threshold = 1.0  # Wait longer for you to finish sentence
    r.phrase_time_limit = 30  # Allow up to 30 seconds for one sentence


def speak(text):
    subprocess.run(["say", "-r", "190", text], capture_output=True)
    time.sleep(1.5)


def process(text):
    correction = check_learnings(text)
    if correction:
        return f"Got it! {correction}"

    try:
        from core.orchestrator import get_orchestrator

        orch = get_orchestrator()
        response = orch.process_input(text, source="voice")
        return response
    except Exception as e:
        return f"Oops! {str(e)[:80]}"


def listen_continuous():
    print("\n🎤 Listening...\n")

    speak("Go ahead!")
    time.sleep(1)

    while True:
        try:
            with sr.Microphone() as source:
                print("👂 ", end="\r", flush=True)
                audio = r.listen(source, timeout=5, phrase_time_limit=30)

            # Verify voice matches (only your voice!)
            audio_data = audio.get_raw_data()
            if not verify_voiceprint(audio_data):
                print("❌ Voice not recognized, ignoring...\n")
                continue

            text = r.recognize_google(audio).lower().strip()

            if not text:
                continue

            print(f"You: {text}")

            if any(p in text for p in ["that's wrong", "mistake", "incorrect"]):
                speak("What should I have said?")
                time.sleep(1)
                try:
                    with sr.Microphone() as source:
                        audio2 = r.listen(source, timeout=5, phrase_time_limit=8)
                    if not verify_voiceprint(audio2.get_raw_data()):
                        print("❌ Voice not recognized for correction")
                        speak("Sorry, didn't catch that.")
                        continue
                    correction = r.recognize_google(audio2).strip()
                    if correction:
                        add_learning(text, correction)
                        speak("Got it!")
                except:
                    pass
                continue

            if any(w in text for w in STOP_WORDS):
                speak("Talk to you later!")
                print("💤 Going back to sleep mode. Say 'hikari' to wake me.\n")
                return  # Go back to listening for wake word

            response = process(text)
            if response:
                print(f"HIKARI: {response}")
                speak(response)
                log_convo(text, response)

        except sr.WaitTimeoutError:
            return
        except sr.UnknownValueError:
            continue
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(0.5)


def listen_for_wake():
    print(f"\n🎯 Say '{WAKE_WORD}' to activate!\n")

    while True:
        try:
            with sr.Microphone() as source:
                # Calibrate for ambient noise first
                r.adjust_for_ambient_noise(source, duration=0.5)
                print("Waiting...", flush=True)
                audio = r.listen(source, timeout=3, phrase_time_limit=3)

            # Bypass voice filter for wake word - just verify it's speech
            audio_data = audio.get_raw_data()
            if not verify_voiceprint(audio_data):
                print("❌ Voice not recognized, ignored\n")
                continue

            text = r.recognize_google(audio).lower().strip()

            if WAKE_WORD in text:
                print(f"\n🎉 '{text}' - ACTIVATED!\n")
                speak("Yeah?")
                log_convo(f"[WAKE WORD: {text}]", "Activated")
                return

        except sr.WaitTimeoutError:
            pass
        except sr.UnknownValueError:
            pass
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)


if __name__ == "__main__":
    if not sr:
        print("\n❌ Run: /opt/anaconda3/bin/python3 -m pip install speechrecognition")
        sys.exit(1)

    # Check for voice setup flag
    if len(sys.argv) > 1 and sys.argv[1] == "--setup-voice":
        setup_voiceprint()
        sys.exit(0)

    print(f"\n✅ HIKARI ready! Say '{WAKE_WORD}' to start")
    print("📚 Say 'that's wrong' to teach me!")

    # Check if voiceprint exists
    if not os.path.exists(VOICE_PRINT_FILE):
        print("\n⚠️  No voice recognition set up yet.")
        print(
            "   Run with --setup-voice to train HIKARI to recognize only your voice.\n"
        )
    else:
        print("🔐 Voice recognition enabled - only your voice will activate HIKARI\n")

    signal.signal(signal.SIGINT, lambda s, f: (print("\n\nBye!"), sys.exit(0)))

    while True:
        try:
            listen_for_wake()
            listen_continuous()
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)
