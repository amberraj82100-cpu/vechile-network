#!/bin/zsh
set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

export TK_SILENCE_DEPRECATION=1

if command -v python3 >/dev/null 2>&1; then
    exec python3 main.py
elif command -v python >/dev/null 2>&1; then
    exec python main.py
else
    echo "Python 3 was not found on PATH. Install Python 3 and try again."
    exit 1
fi
