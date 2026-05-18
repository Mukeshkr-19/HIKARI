# HIKARI v3 - Personal AI Assistant

## Vision
The ultimate personal AI assistant that runs 24/7, learns everything about you, controls your Mac, automates your home, and feels like a real companion — not like Siri.

**Core Principles:**
- Privacy-first: All processing happens locally on your Mac
- Speed: Instant responses, never makes you wait
- Personality: Evolves with you, remembers everything, emotionally intelligent
- Capability: Controls your entire digital life + smart home

## Architecture

```
hikari/
├── brain/                    # HIKARI's persistent memory & learning
│   ├── memory.py            # Long-term memory system
│   ├── personality.py       # Adaptive personality engine
│   ├── emotional_iq.py     # Emotion detection & response adaptation
│   └── knowledge.py         # Knowledge graph of your world
├── voice/                    # Voice I/O - always listening
│   ├── wake_word.py        # Local wake word detection (Pyaudio)
│   ├── stt.py              # Speech-to-text (Whisper local)
│   └── tts.py              # Text-to-speech (macOS say)
├── mac/                      # Mac integration layer
│   ├── apps.py             # App launching & control
│   ├── calendar.py         # Calendar events
│   ├── mail.py            # Email access
│   ├── notes.py            # Notes integration
│   ├── reminders.py        # Reminders integration
│   └── system.py           # System control ( brightness, volume)
├── agents/                   # Task-specific agents
│   ├── router.py           # Routes tasks to right agent
│   ├── research.py         # Web search & research
│   ├── files.py            # File operations
│   ├── smart_home.py       # HomeKit/smart device control
│   └── automation.py       # Task automation
├── daemon/                   # 24/7 background service
│   ├── hikari_service.py   # Main daemon service
│   └── tray.py             # System tray icon & menu
├── hikari.py                 # Main entry point
└── server.py                 # WebSocket for phone connectivity
```

## Features

### 1. Always Listening Brain
- Wake word: "Hey HIKARI" or custom
- Local processing — no cloud for wake detection
- Learns your voice patterns
- Remembers everything you've ever said

### 2. Personal Memory
- Stores every conversation
- Learns your preferences, habits, relationships
- Builds a knowledge graph of your life
- Adapts personality based on interactions

### 3. Mac Control
- Open/close apps
- Read calendar, email, notes, reminders
- Control system settings (volume, brightness)
- Window management
- File operations

### 4. Smart Home Integration
- HomeKit device control
- Voice control for lights, thermostat, etc.
- Automation rules
- Energy monitoring

### 5. Emotional Intelligence
- Detects mood from voice/text
- Adapts responses to your emotional state
- Supports when you're sick (lower sensitivity)
- Learns communication style

### 6. 24/7 Background Service
- Runs as system service
- System tray icon
- Starts on login
- Always available

## Quick Start

```bash
cd HIKARI
source .venv/bin/activate
pip install -r requirements.txt

# Run HIKARI
python3 hikari.py

# Or install as service (24/7)
python3 daemon/hikari_service.py --install
```

## Voice Commands
- "Hey HIKARI" - Wake up
- "What's on my calendar?" - Calendar info
- "Send an email" - Email dictation
- "Turn off the lights" - Smart home
- "Remember I prefer tea" - Store preference
- "Who am I?" - See what HIKARI knows

## Privacy
- All voice processing done locally (Whisper)
- No data sent to cloud for AI responses (configurable)
- API keys stored in .env, never in code
- Optional local LLM via Ollama

## Tech Stack
- Python 3.12+
- Whisper (local STT)
- Ollama (local LLM option)
- HomeKit (smart home)
- AppleScript (Mac integration)
- WebSocket (phone connectivity)
