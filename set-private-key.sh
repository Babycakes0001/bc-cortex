#!/bin/bash
# BC Cortex — set the passphrase that unlocks your 'private' folder in the viewer.
# Stored ONLY as a salted one-way hash. Your actual passphrase is never written to
# disk, never logged, never leaves this machine. Restart the server to re-lock.
set -euo pipefail
KEYFILE="$(cd "$(dirname "$0")" && pwd)/.private-key"

read -r -s -p "Set your private passphrase: " p; echo
[ -n "$p" ] || { echo "✗ empty — aborted."; exit 1; }
read -r -s -p "Confirm passphrase:        " p2; echo
[ "$p" = "$p2" ] || { echo "✗ didn't match — aborted."; exit 1; }

salt="$(openssl rand -hex 16)"
hash="$(printf '%s' "${salt}${p}" | shasum -a 256 | cut -d' ' -f1)"
printf '%s:%s\n' "$salt" "$hash" > "$KEYFILE"
chmod 600 "$KEYFILE"
unset p p2
echo "✓ Passphrase set (stored hashed at .private-key, chmod 600, gitignored)."
echo "  Unlock in the viewer with the 🔒 button. Reload re-locks."
