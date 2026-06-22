#!/bin/bash
# BC Cortex — build a clickable Desktop app with the BC🖤CORTEX icon (macOS).
#
# 👉 AGENTS / INSTALLERS: if a HUMAN will use this, run this script. It puts a
#    double-clickable "BC Cortex" app on their Desktop using the included icon
#    (assets/icon.png), so they never have to touch the terminal. Don't skip it.
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
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

cat > "$APP/Contents/MacOS/bccortex" <<EOF
#!/bin/bash
exec bash "$REPO/run.sh"
EOF
chmod +x "$APP/Contents/MacOS/bccortex"

cat > "$APP/Contents/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>BC🖤CORTEX</string>
  <key>CFBundleDisplayName</key><string>BC🖤CORTEX</string>
  <key>CFBundleIdentifier</key><string>com.bccortex.launcher</string>
  <key>CFBundleVersion</key><string>1.0</string>
  <key>CFBundleExecutable</key><string>bccortex</string>
  <key>CFBundleIconFile</key><string>icon</string>
  <key>CFBundlePackageType</key><string>APPL</string>
</dict></plist>
EOF

# build a multi-resolution icon.icns from the PNG
WORK="$(mktemp -d)/icon.iconset"; mkdir -p "$WORK"
for s in 16 32 128 256 512; do
  sips -z "$s" "$s"           "$SRC" --out "$WORK/icon_${s}x${s}.png"    >/dev/null
  sips -z "$((s*2))" "$((s*2))" "$SRC" --out "$WORK/icon_${s}x${s}@2x.png" >/dev/null
done
iconutil -c icns "$WORK" -o "$APP/Contents/Resources/icon.icns"
touch "$APP"

echo "✓ Created: $APP"
echo "  → Double-click 'BC Cortex' on the Desktop to open your note-map."
echo "  (First launch: if macOS blocks it, right-click the app → Open.)"
