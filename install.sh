#!/usr/bin/env bash
# HIKARI — portable setup (macOS / Linux). Run from the repo root after git clone.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

echo "=== HIKARI setup ==="
echo "Repository: $REPO_ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is required." >&2
  exit 1
fi

PY_VER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
echo "Python: $(python3 --version) (need 3.10+; 3.12 recommended)"

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment in .venv ..."
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip wheel setuptools
pip install -r requirements.txt

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp .env.example .env
  echo ""
  echo "Created .env from .env.example"
  echo "Edit .env and add at least one AI provider key (see README)."
fi

chmod +x bin/Hikari 2>/dev/null || true
chmod +x "$REPO_ROOT/scripts/install-hikari-login-agent.sh" \
  "$REPO_ROOT/scripts/uninstall-hikari-login-agent.sh" 2>/dev/null || true

# Optional: global command — type Hikari from any directory
HB="$HOME/bin"
mkdir -p "$HB"
ln -sf "$REPO_ROOT/bin/Hikari" "$HB/Hikari"
ln -sf "$REPO_ROOT/bin/Hikari" "$HB/hikari"
if [[ ":$PATH:" != *":$HB:"* ]]; then
  echo ""
  echo "To run Hikari from anywhere, add this line to ~/.zshrc (or ~/.bashrc):"
  echo "  export PATH=\"\$HOME/bin:\$PATH\""
  echo ""
  echo "Then restart the terminal or:  export PATH=\"\$HOME/bin:\$PATH\""
fi

echo ""
echo "=== Done ==="
echo "Activate the environment:"
echo "  source .venv/bin/activate"
echo ""
echo "CLI from repo folder:"
echo "  ./bin/Hikari"
echo ""
echo "After PATH includes \$HOME/bin:"
echo "  Hikari"
echo ""
