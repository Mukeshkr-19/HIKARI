## Work done (April 2026)

This file documents the stabilization + voice-lock work performed to align HIKARI with the “JARVIS-like” vision: wake-word daemon, local-first data, and “only responds to you”.

### What was broken

- **Python environment mismatch**: system `python3` was **3.14**, but the project virtualenv is **3.12**. Several audio/ML dependencies behave poorly on 3.14.
- **Missing deps in `.venv`**: `feedparser` and `pytest` were missing, so `src/hikari.py` didn’t start.
- **Whisper package mismatch**: `whisper==1.1.10` installs a different `whisper.py` module that does not provide `load_model()`.
- **CLI crash**: `src/hikari_cli.py` monkeypatched `builtins.print`, which caused `numba` (pulled by Whisper) to crash on import.

### Fixes applied

- **Installed missing deps into `.venv`** so `src/hikari.py` runs.
- **Installed correct Whisper** implementation:
  - Added `openai-whisper` to `requirements.txt`
  - Verified `whisper.load_model` exists after install
- **Prevented hangs in non-voice modes**:
  - Added `enable_mic` flag to `core.voice.VoiceSystem`
  - Threaded through `core.orchestrator.get_orchestrator(enable_mic=...)`
  - `src/hikari.py` now only enables mic warmup when `--voice` is used
- **Fixed CLI crash**:
  - Removed `builtins.print` monkeypatch
  - CLI now initializes orchestrator with `enable_mic=False`

### “Only responds to you” (speaker verification)

Important: **VibeVoice is an ASR model** (speech-to-text). It is not a speaker-verification system by itself. For the “only my voice can activate” requirement, we implemented **local speaker verification** using embeddings.

- Added `core/speaker_auth.py`:
  - Uses **SpeechBrain ECAPA** embeddings (`speechbrain/spkrec-ecapa-voxceleb`)
  - Stores only the **embedding** locally in `data/voice_auth.json`
  - Keeps HuggingFace model cache inside the repo: `data/hf_cache/`
- Updated `src/hikari_daemon.py`:
  - Added `--enroll-voice` (alias: `--setup-voice`) to enroll your voice
  - Wake-word + command loop now calls `verify_speaker(audio)` and **ignores other speakers**
  - Fail-safe: if verification errors, daemon does **not** respond
- Updated `.gitignore`:
  - `data/voice_auth.json` ignored (personal biometric)
  - `data/hf_cache/` ignored (large model cache)

### How to run (recommended)

- **Text mode**:
  - `.venv/bin/python src/hikari.py --text`
- **CLI mode**:
  - `.venv/bin/python src/hikari_cli.py`
- **Server-only**:
  - `.venv/bin/python src/hikari.py --server --port 8765`
- **Always-on wake-word daemon** (the “class-safe” mode):
  - Enroll once: `.venv/bin/python src/hikari_daemon.py --enroll-voice`
  - Run: `.venv/bin/python src/hikari_daemon.py`

### Test status

- `pytest` now passes: **31 passed**.

### GitHub-ready packaging + README (follow-up)

- **Portable install**: added `install.sh` (uses `SCRIPT_DIR` / repo root — **no user-specific paths**).
- **npm shortcuts**: root `package.json` with `npm run setup`, `start`, `voice`, `server`, `daemon`, `enroll`.
- **README rewrite**: single source of truth for clone → `./install.sh` → `source .venv/bin/activate` → modes; removed hardcoded `/Users/...` paths.
- **Public safety**: scrubbed placeholder secret from `.env.example` (`WEATHER_API_KEY` must be filled by each user).
- **Daemon data paths**: `src/hikari_daemon.py` now writes `data/` and `logs/` under **repository root** (not `src/data`).
- **Web UI**: fixed HTTP routes on modern Python by always passing `process_request` to `websockets.serve`; added hologram HUD at **`/hud`**.

