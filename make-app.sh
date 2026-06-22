#!/bin/bash
# BC Cortex — build a clickable Desktop app with the BC🖤CORTEX icon (macOS).
#
# 👉 AGENTS / INSTALLERS: if a HUMAN will use this, run this script. It puts a
#    double-clickable "BC Cortex" app on their Desktop using the included icon
#    (assets/icon.png), so they never touch the terminal. Don't skip it.
set -euo pipefail
REPO="$(cd "$(dirname "$0")" && pwd)"
SRC="$REPO/assets/icon.png"
APP="$HOME/Desktop/BC Cortex.app"

if [ "$(uname)" != "Darwin" ]; then
  echo "make-app.sh builds a macOS .app. On Linux/Windows, launch with: bash run.sh"
  exit 0
fi
[ -f "$SRC" ] || { echo "missing $SRC"; exit 1; }

rm -rf "$APP"
# Build a NATIVE AppleScript app (universal binary → no Rosetta prompt) that
# launches BC Cortex. A hand-rolled .app with a shell-script executable triggers
# a bogus "install Rosetta" prompt on Apple Silicon — osacompile avoids that.
osacompile -o "$APP" -e "do shell script \"bash '$REPO/run.sh'\""

# swap in the BC🖤CORTEX icon (osacompile apps use applet.icns)
WORK="$(mktemp -d)/icon.iconset"; mkdir -p "$WORK"
for s in 16 32 128 256 512; do
  sips -z "$s" "$s"             "$SRC" --out "$WORK/icon_${s}x${s}.png"    >/dev/null
  sips -z "$((s*2))" "$((s*2))" "$SRC" --out "$WORK/icon_${s}x${s}@2x.png" >/dev/null
done
iconutil -c icns "$WORK" -o "$APP/Contents/Resources/applet.icns"
touch "$APP"

echo "✓ Created: $APP"
echo "  → Double-click 'BC Cortex' on the Desktop to open your note-map."
echo "  (First launch: if macOS blocks it, right-click the app → Open.)"
