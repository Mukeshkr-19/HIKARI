#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAUNCHER="$REPO_ROOT/bin/Hikari"

if [[ ! -x "$LAUNCHER" ]]; then
  chmod +x "$LAUNCHER"
fi

if [[ -n "${HIKARI_CLI_DIR:-}" ]]; then
  CLI_DIR="$HIKARI_CLI_DIR"
elif [[ ":$PATH:" == *":$HOME/.local/bin:"* ]]; then
  CLI_DIR="$HOME/.local/bin"
elif [[ ":$PATH:" == *":$HOME/bin:"* ]]; then
  CLI_DIR="$HOME/bin"
else
  CLI_DIR="$HOME/.local/bin"
fi

mkdir -p "$CLI_DIR"
ln -sf "$LAUNCHER" "$CLI_DIR/hikari"
ln -sf "$LAUNCHER" "$CLI_DIR/Hikari"

echo "Installed HIKARI CLI:"
echo "  $CLI_DIR/hikari -> $LAUNCHER"
echo "  $CLI_DIR/Hikari -> $LAUNCHER"

if [[ ":$PATH:" != *":$CLI_DIR:"* ]]; then
  echo ""
  echo "Add this to your shell config, then restart Terminal:"
  echo "  export PATH=\"$CLI_DIR:\$PATH\""
fi

echo ""
echo "Try:"
echo "  hikari --doctor"
