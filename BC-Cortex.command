#!/bin/bash
# BC🖤CORTEX — double-click launcher (macOS).
#
# Double-click this file in Finder to build your note-map and open it in your
# browser. (First time only: if macOS blocks it, right-click → Open, then "Open".)
cd "$(dirname "$0")" || exit 1
bash run.sh
echo
echo "🖤 BC Cortex is open in your browser. You can close this window."
