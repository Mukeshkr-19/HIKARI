#!/usr/bin/env bash
# Install a Launch Agent so HIKARI's wake-word daemon starts at login (macOS only).
# Requires: enrollment first — only your voice activates HIKARI.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PY="$REPO_ROOT/.venv/bin/python"
DAEMON="$REPO_ROOT/src/hikari_daemon.py"
PLIST_DST="$HOME/Library/LaunchAgents/com.hikari.wake.plist"
LOG_DIR="$HOME/Library/Logs"
OUT_LOG="$LOG_DIR/hikari-daemon.stdout.log"
ERR_LOG="$LOG_DIR/hikari-daemon.stderr.log"
LABEL="com.hikari.wake"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This installer is for macOS only." >&2
  exit 1
fi

if [[ ! -x "$PY" ]]; then
  echo "Missing venv Python: $PY — run ./install.sh first." >&2
  exit 1
fi

if [[ ! -f "$DAEMON" ]]; then
  echo "Missing daemon: $DAEMON" >&2
  exit 1
fi

if [[ ! -f "$REPO_ROOT/data/voice_auth.json" ]]; then
  echo ""
  echo "Warning: No speaker enrollment at data/voice_auth.json"
  echo "  For only-you mode, enroll once:"
  echo "    cd \"$REPO_ROOT\" && .venv/bin/python src/hikari_daemon.py --enroll-voice"
  echo ""
  if [[ ! -t 0 ]]; then
    echo "Non-interactive shell: enroll first, then re-run this script." >&2
    exit 1
  fi
  read -r -p "Continue without enrollment? Anyone's voice may wake HIKARI. [y/N] " ans || true
  if [[ "${ans:-}" != "y" && "${ans:-}" != "Y" ]]; then
    exit 1
  fi
fi

mkdir -p "$LOG_DIR"

# Unload previous job if present (ignore errors)
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl unload "$PLIST_DST" 2>/dev/null || true

cat >"$PLIST_DST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>
  <key>LimitLoadToSessionType</key>
  <string>Aqua</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>ThrottleInterval</key>
  <integer>30</integer>
  <key>WorkingDirectory</key>
  <string>$REPO_ROOT</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin</string>
    <key>HIKARI_HOME</key>
    <string>$REPO_ROOT</string>
    <key>HIKARI_QUIET</key>
    <string>1</string>
  </dict>
  <key>ProgramArguments</key>
  <array>
    <string>$PY</string>
    <string>-E</string>
    <string>$DAEMON</string>
  </array>
  <key>StandardOutPath</key>
  <string>$OUT_LOG</string>
  <key>StandardErrorPath</key>
  <string>$ERR_LOG</string>
</dict>
</plist>
EOF

chmod 644 "$PLIST_DST"

# Load for current GUI session
if launchctl bootstrap "gui/$(id -u)" "$PLIST_DST" 2>/dev/null; then
  :
else
  launchctl load -w "$PLIST_DST" || {
    echo "launchctl failed. Try: launchctl load -w $PLIST_DST" >&2
    exit 1
  }
fi

echo ""
echo "OK: HIKARI wake daemon will start at login and stay running."
echo "   Repo:     $REPO_ROOT"
echo "   Logs:     $OUT_LOG"
echo "   Stop now:  launchctl bootout gui/$(id -u)/$LABEL"
echo "   Uninstall: $REPO_ROOT/scripts/uninstall-hikari-login-agent.sh"
echo ""
echo "Grant Microphone (once): System Settings → Privacy & Security → Microphone"
echo "  Enable for Terminal if you tested there; for background runs, you may need to"
echo "  allow the Python binary under .venv (macOS will prompt on first mic use)."
echo ""
