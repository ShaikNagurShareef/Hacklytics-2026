#!/bin/bash
# Redact exposed API key from all git history.
# Run from repo root: HACKGT (parent of MEDORA)
# Usage: ./MEDORA/backend/scripts/redact_api_key.sh

set -e
# From MEDORA/backend/scripts go up to repo root (HACKGT)
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$REPO_ROOT"

# Set the key to redact via env to avoid committing it again, e.g.:
#   EXPOSED_API_KEY='paste_key_here' ./MEDORA/backend/scripts/redact_api_key.sh
OLD="${EXPOSED_API_KEY:?Set EXPOSED_API_KEY to the key to redact from history}"
NEW='REDACTED'

echo "Rewriting history to replace exposed API key in all commits..."
git filter-branch --force --tree-filter "
  find . -type f \( -name '*.py' -o -name '*.env' \) 2>/dev/null | while read f; do
    if grep -q '$OLD' \"\$f\" 2>/dev/null; then
      if sed --version 2>/dev/null | grep -q GNU; then
        sed -i \"s|$OLD|$NEW|g\" \"\$f\"
      else
        sed -i.bak \"s|$OLD|$NEW|g\" \"\$f\" && rm -f \"\$f.bak\"
      fi
    fi
  done
" --tag-name-filter cat -- --all

echo "Done. Next steps:"
echo "  1. git push --force --all origin"
echo "  2. git push --force --tags origin  (if you have tags)"
echo "  3. Revoke this key in Google AI Studio and create a new one."
echo "  4. Tell collaborators to re-clone or run: git fetch && git reset --hard origin/<branch>"
