#!/usr/bin/env bash
# Remove HIKARI Launch Agent (macOS).
set -euo pipefail

PLIST_DST="$HOME/Library/LaunchAgents/com.hikari.wake.plist"
LABEL="com.hikari.wake"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This script is for macOS only." >&2
  exit 1
fi

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl unload "$PLIST_DST" 2>/dev/null || true

if [[ -f "$PLIST_DST" ]]; then
  rm -f "$PLIST_DST"
  echo "Removed $PLIST_DST"
else
  echo "No plist at $PLIST_DST"
fi
