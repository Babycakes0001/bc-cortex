#!/bin/bash
# BC Cortex — build the map and open it in your browser.
set -euo pipefail
cd "$(dirname "$0")"
PORT="${BC_CORTEX_PORT:-9091}"
URL="http://127.0.0.1:${PORT}/"

python3 index.py

# start the local server if it isn't already up
if ! curl -s -m 2 -o /dev/null "$URL"; then
  nohup python3 server.py >/dev/null 2>&1 &
  sleep 1
fi

# open in the default browser (macOS: open · Linux: xdg-open)
if command -v open >/dev/null 2>&1;       then open "$URL"
elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL"
else echo "Open $URL in your browser."
fi
