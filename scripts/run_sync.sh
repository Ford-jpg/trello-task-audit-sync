#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

python3 src/sync_weekly.py "$@"
