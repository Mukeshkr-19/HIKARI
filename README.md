# HIKARI

**Local-first “JARVIS-style” assistant for macOS** — wake word, speaker lock, multi-agent brain, Mac automation, learning from corrections, and a phone HUD that talks to your Mac.

Everything you need lives **inside this repository** after you clone it (virtualenv, `data/`, `.env`). No hardcoded machine paths.

---

## Requirements

- **macOS** (primary target; voice + `say` TTS + AppleScript automation)
- **Python 3.10+** (3.12 recommended)
- **Node.js 18+** (optional — only if you use `npm run …` shortcuts)

---

## Install (any Mac — portable)

### Option A — `git clone` + install script (recommended)

```bash
git clone https://github.com/Mukeshkr-19/HIKARI.git
cd HIKARI
chmod +x install.sh
./install.sh
```

This creates `.venv` in the repo, installs Python dependencies, and copies `.env.example` → `.env` if `.env` is missing.

### Option B — One-liner (downloads `install.sh` from GitHub)

Replace `main` with your branch if needed:

```bash
curl -fsSL https://raw.githubusercontent.com/Mukeshkr-19/HIKARI/main/install.sh | bash
```

Then `cd` into the folder you cloned (the script is meant to be run **inside** the repo after clone; the canonical flow is still **clone first**, then `./install.sh` from the repo root).

**Safest one-liner:**

```bash
git clone https://github.com/Mukeshkr-19/HIKARI.git && cd HIKARI && chmod +x install.sh && ./install.sh
```

### Option C — npm scripts (shortcuts)

After `git clone` and `cd HIKARI`:

```bash
npm install
npm run setup
```

Then use:

| Command | What it runs |
|--------|----------------|
| `npm run start` | Text UI (`src/hikari.py --text`) |
| `npm run voice` | Voice UI with wake word + sleep (`--voice`) |
| `npm run server` | WebSocket server + phone HUD (`--server`) |
| `npm run daemon` | Always-on wake-word daemon |
| `npm run enroll` | Speaker enrollment (`--enroll-voice`) |

### Run `Hikari` from anywhere (terminal)

`./install.sh` symlinks `bin/Hikari` into **`~/bin`**. Add this once to `~/.zshrc` (or `~/.bashrc`) if it is not already there:

```bash
export PATH="$HOME/bin:$PATH"
```

Restart the terminal, then from **any directory**:

```bash
Hikari
```

The launcher finds your clone via the symlink (or set `HIKARI_HOME` to the repo path if you move the project).  
In the CLI, **HUD URLs are printed** (Local + Network). Copy them, or type **`ui`** to open the HUD in your default browser. Change the port with `HIKARI_PORT` (default **8765**).

---

## Configuration (everyone uses their own keys)

1. Copy env template:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add **at least one** AI provider key (see comments in `.env.example`).

**Never commit `.env`** — public collaborators must use **their** keys. Biometric enrollment files under `data/` are gitignored as well.

---

## How to run

Activate the venv (from repo root):

```bash
source .venv/bin/activate
```

### Text mode

```bash
python src/hikari.py --text
```

### Voice mode (wake “hikari”, say “bye” to sleep, speaker-locked if enrolled)

```bash
python src/hikari.py --voice
```

### Always-on daemon (best for “always listening, only my voice”)

```bash
python src/hikari_daemon.py --enroll-voice   # once
python src/hikari_daemon.py
```

### Start the daemon automatically at login (macOS)

Install a **Launch Agent** so you do not have to run anything manually each day:

```bash
chmod +x scripts/install-hikari-login-agent.sh scripts/uninstall-hikari-login-agent.sh
./scripts/install-hikari-login-agent.sh
```

- **What it runs by default:** `src/hikari_simple.py` (simple always-on listener; STT-based wake phrase)
- **Logs:** `~/Library/Logs/hikari-assistant.stdout.log` and `…stderr.log`
- **Stop until next login:** `launchctl bootout gui/$(id -u)/com.hikari.assistant`
- **Remove auto-start:** `./scripts/uninstall-hikari-login-agent.sh`

Allow **Microphone** for the app that runs the daemon (often **Terminal** during tests; after login, macOS may list **Python** under `.venv` — enable it when prompted).

### Server + phone (same Wi‑Fi)

```bash
python src/hikari.py --server --port 8765
```

On your phone, open (replace with your Mac’s LAN IP shown in the terminal):

- `http://<your-mac-ip>:8765/hud` — **hologram HUD**
- `http://<your-mac-ip>:8765/connect` — compact connect UI
- `http://<your-mac-ip>:8765/qr` — QR code

Pair with the **6-digit code** printed in the terminal.

**Remote use (not on same Wi‑Fi):** use [Tailscale](https://tailscale.com/) or a tunnel (e.g. Cloudflare Tunnel) so your phone can reach your Mac securely. That is outside this repo but is the standard way to get “Iron Man phone → home Mac” without exposing raw ports.

---

## What’s in this project (current)

| Path | Role |
|------|------|
| `src/hikari.py` | Main entry: `--text` / `--voice` / `--server` |
| `src/hikari_daemon.py` | Always-on wake word + speaker verification |
| `src/hikari_cli.py` | Minimal banner CLI |
| `core/orchestrator.py` | Agents, routing, Mac actions |
| `core/speaker_auth.py` | Speaker embedding lock (local `data/`) |
| `src/server.py` | WebSocket + HTTP (`/connect`, `/hud`, `/qr`) |
| `data/` | Local state (gitignored where private) |
| `docs/` | Extra docs + `docs/WORK_DONE.md` changelog |

AI routing lives in **`core/router.py`**. Episodic turns are appended under **`data/episodes/`** (daily JSONL, local-only) in addition to `data/memory.json`.

---

## Learning from mistakes

Say **“that’s wrong”** in the wake-word flow and the daemon will ask for a correction and save it under `data/` (see daemon + orchestrator). Teach corrections in voice or refine in text mode.

---

## Security note

**Full “access my entire Mac”** always implies **strong trust**: keep `.env` secret, use speaker enrollment, and review Mac automation in `core/mac_integration.py` / `agents/system.py`. This README does not grant magical bypass of macOS permissions — Screen Recording, Accessibility, and Microphone must still be allowed in **System Settings** when macOS prompts you.

---

## License

See `LICENSE` in the repository (or add one if missing — MIT is common for public projects).

---

## Troubleshooting

### `Hikari` seems stuck, or Python errors about `site` (Conda users)

If you use **Anaconda/Miniconda** with `(base)` active, Conda can set `PYTHONHOME` / `PYTHONPATH` and **break** the project’s `.venv` Python (including `import site`).

**Fix:** run `conda deactivate` before `Hikari`, **or** the `bin/Hikari` launcher clears those variables and runs `python -E` — update to the latest `bin/Hikari` from this repo and re-run `./install.sh` so `~/bin/Hikari` points at it.

**Do not** press **Ctrl+C** during the first ~20 seconds while models and the orchestrator load; wait until you see the HUD URLs.

### `Hikari` command not found

Ensure `export PATH="$HOME/bin:$PATH"` is in `~/.zshrc`, then run `./install.sh` once from your clone so `~/bin/Hikari` is created.

---

## More docs

- [docs/README.md](docs/README.md) — feature overview  
- [docs/QUICKSTART.md](docs/QUICKSTART.md) — quick paths  
- [docs/WORK_DONE.md](docs/WORK_DONE.md) — technical changelog  
