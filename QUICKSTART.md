# HIKARI v2.0 - Quick Start Guide

## Your Personal JARVIS is Ready

HIKARI v2.0 is a fully autonomous, multi-agent AI assistant that:
- **Knows you** - Learns your voice, habits, preferences, relationships
- **Anticipates needs** - Proactive suggestions based on your patterns
- **Adapts to you** - Evolves personality, detects emotions, supports when sick
- **Works everywhere** - Laptop brain + phone/watch interface
- **Remembers everything** - Semantic memory with deep context retrieval

## Setup (5 minutes)

### 1. Get API Keys (at least one)

**Recommended: Google AI Studio** (best free tier, 1M context)
- Go to: https://aistudio.google.com/app/apikey
- Click "Create API Key"
- Copy the key

**Alternative: Groq** (fastest, 300+ tokens/sec)
- Go to: https://console.groq.com/keys
- Create API key

### 2. Configure

```bash
cd HIKARI
source .venv/bin/activate

# Edit .env file
nano .env  # or use any editor

# Add your API key(s):
GOOGLE_AI_STUDIO_KEY=your-key-here
# GROQ_API_KEY=your-key-here
```

### 3. Run

```bash
# Text mode (easiest to start)
python3 hikari.py --text

# Voice mode
python3 hikari.py

# Server only (for phone connections)
python3 hikari.py --server
```

## Phone Connection

1. Start HIKARI on laptop
2. Note the IP shown: `http://192.168.x.x:8765/connect`
3. Open that URL on your phone's browser
4. Enter the 6-digit pairing code
5. Done! Your phone is now connected to HIKARI

**Or scan the QR code:** `http://192.168.x.x:8765/qr`

## Voice Activation

- **Wake Word**: Say "Hikari" to activate
- **Codename**: Set your own private fallback in `.env` for sick or noisy environments
- **Clap Detection**: Double-clap to activate (when enabled)

## Commands

### Basic
- "What's the weather?" - Weather info
- "Open Safari" - Launch apps
- "Open YouTube" - Open websites
- "What time is it?" - Current time
- "What's the news?" - Latest headlines
- "Morning briefing" - Full daily update

### Memory & Learning
- "Remember that I live in Chennai" - Store facts
- "What do you know about me?" - View profile
- "What have we talked about?" - Search memory
- "My name is Alex" - HIKARI learns automatically

### Health
- "I'm not feeling well" - Activates sick mode
- HIKARI automatically detects when you're sick
- Lowers voice sensitivity, provides support
- Tracks health episodes over time

### System
- "Status" - Full system report
- "Exit" / "Goodbye" - Shut down

## What HIKARI Learns About You

1. **Voice** - Stores voice patterns, adapts when sick
2. **Name & Location** - From conversations
3. **Preferences** - Tools, apps, communication style
4. **Relationships** - People you mention
5. **Projects & Interests** - What you work on
6. **Daily Patterns** - When you do things
7. **Emotions** - Mood tracking and support
8. **Health** - Sick episodes, recovery tracking

## Intelligence Systems (24 Total)

| System | What It Does |
|--------|-------------|
| AI Router | Routes to best AI provider (Google, Groq, OpenRouter, etc.) |
| Voice Memory | Learns your voice, adapts when sick |
| User Profile | Learns habits, preferences, relationships |
| Emotional IQ | Detects mood, adapts responses |
| Proactive Intel | Anticipates needs, suggests actions |
| Knowledge Graph | Maps your world (people, projects, interests) |
| Adaptive Personality | Evolves communication style with you |
| Health Awareness | Detects sickness, provides support |
| Semantic Memory | Deep conversation search and context |
| Scheduler | Proactive alerts, scheduled tasks |
| Codename System | Multi-codename, context-aware auth |
| Skill System | Extensible capabilities |
| 6 Agents | Voice, Research, Files, System, Code, Memory |
| WebSocket Server | Cross-device connectivity |

## File Structure

```
hikari/
├── core/              # Intelligence systems (10 files)
├── agents/            # Autonomous agents (7 files)
├── security/          # Authentication & policies (2 files)
├── skills/            # Extensible skills (1 file)
├── hikari-frontend/   # Next.js PWA for phone
├── data/              # Runtime data (auto-created)
├── hikari.py          # Main entry point
├── core/server.py     # WebSocket + mobile web UI
└── install.sh           # One-command setup
```

## Troubleshooting

**No audio input:**
```bash
# macOS: System Preferences > Security > Microphone
brew install portaudio && pip install pyaudio
```

**AI responses fail:**
- Check `.env` has at least one API key
- Run `python3 hikari.py --text` for detailed logs

**Phone won't connect:**
- Same WiFi network required
- Check firewall allows port 8765
- Use `ifconfig` to find laptop IP

## Pro Tips

1. **Talk to HIKARI naturally** - It learns from every conversation
2. **Use your private codename** when voice isn't working (sick, noisy)
3. **Ask "what do you know about me"** to see what it's learned
4. **Say "morning briefing"** for a complete daily update
5. **Check status** anytime with "status" command

## Next Steps

1. Add more API keys for better reliability
2. Customize codename in `.env`
3. Add your own skills in `skills/`
4. Build custom agents in `agents/`

---

**Your personal HIKARI assistant is ready.**
