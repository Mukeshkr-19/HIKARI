# HIKARI Architecture Notes

This file describes the current repository layout and operating model. It is public project-facing documentation; private recovery notes live in `HIKARI-private/docs/` outside Git.

## Vision

HIKARI is a local-first personal AI assistant for macOS with:

- text and server modes through `hikari.py`
- voice/daemon services under `services/`
- multi-agent task routing under `agents/`
- core intelligence, memory, server, and integrations under `core/`
- optional phone/browser frontend under `hikari-frontend/`
- private live neural brain outside Git

## Current Architecture

```text
HIKARI/
├── agents/                  # Voice, research, files, system, code, memory agents
├── bin/                     # Launchers
├── config/                  # Provider config
├── core/
│   ├── orchestrator.py      # Central coordinator
│   ├── router.py            # Multi-provider AI routing
│   ├── server.py            # HTTP/WebSocket server: /api/status, /connect, /qr
│   ├── voice.py             # Speech I/O helpers
│   ├── memory.py            # JSON memory fallback
│   ├── neural_memory/       # SQLite graph memory subsystem
│   ├── neural_memory_bridge.py
│   ├── personality.py
│   ├── mac_control.py
│   └── smart_home.py
├── docs/                    # Public docs
├── hikari-frontend/         # Next.js frontend
├── scripts/                 # Login-agent helpers
├── security/                # Auth helpers
├── services/                # Daemon/tray/always-on entrypoints
├── skills/                  # Skill system
├── tests/                   # Pytest suite
├── hikari.py                # Main entrypoint
├── install.sh
├── package.json
├── requirements-dev.txt
└── requirements.txt
```

## Private Runtime Architecture

Private files are not part of the public repo:

```text
/Users/mukeshkrishnamurthy/Documents/HIKARI-projects/HIKARI-private/
├── docs/
├── live-brain/
├── monthly-backups/
├── brain-backups/
├── legacy-data/
└── scripts/
```

The live brain is reached through:

```text
/Users/mukeshkrishnamurthy/.hikari/brain
```

which points to:

```text
/Users/mukeshkrishnamurthy/Documents/HIKARI-projects/HIKARI-private/live-brain
```

## Current Commands

```bash
cd /Users/mukeshkrishnamurthy/Documents/HIKARI-projects/HIKARI

.venv/bin/python hikari.py --help
.venv/bin/python hikari.py --doctor
.venv/bin/python hikari.py --doctor-full
.venv/bin/python hikari.py --install-cli
.venv/bin/python hikari.py --uninstall-cli
.venv/bin/python hikari.py --text
.venv/bin/python hikari.py --server --host 127.0.0.1 --port 9876
.venv/bin/python hikari.py --daemon
.venv/bin/python hikari.py --tray
.venv/bin/python hikari.py --install
```

After CLI install, these global shell commands work from any directory:

```bash
hikari --doctor
Hikari --doctor
```

Speaker-locked daemon:

```bash
.venv/bin/python services/hikari_daemon.py --enroll-voice
.venv/bin/python services/hikari_daemon.py
```

Frontend:

```bash
cd hikari-frontend
npm run lint
npm run build
```

## Known Stable Baseline

- `pytest tests -q` passes.
- `hikari.py --help` and `hikari --help` work.
- `hikari.py --doctor` and `hikari --doctor` work.
- text mode status works.
- server `/api/status` works.
- frontend lint/build passes.
- neural memory connects outside restricted sandbox.

## Important Caution

Do not move private brain/docs into Git. Do not clean neural-memory data without a backup first. Do not add commands to docs unless they have been verified.
