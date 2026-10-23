#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: deploy-backend.sh <staging-dir> <backend-dir>" >&2
  exit 2
fi

STAGING_DIR=${1%/}
BACKEND_DIR=${2%/}

if [[ -z "$STAGING_DIR" || -z "$BACKEND_DIR" || "$BACKEND_DIR" == "/" ]]; then
  echo "Staging and backend directories must be non-root paths." >&2
  exit 2
fi
if [[ ! -d "$STAGING_DIR/app" || ! -f "$STAGING_DIR/requirements.txt" ]]; then
  echo "Staged backend app or requirements.txt not found under $STAGING_DIR" >&2
  exit 1
fi

mkdir -p -- "$BACKEND_DIR/app"
find "$BACKEND_DIR/app" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +
cp -a -- "$STAGING_DIR/app/." "$BACKEND_DIR/app/"
cp -- "$STAGING_DIR/requirements.txt" "$BACKEND_DIR/requirements.txt"

case "$STAGING_DIR" in
  /home/test/.deploy/backend-*) rm -rf -- "$STAGING_DIR" ;;
esac

echo "Backend files uploaded to $BACKEND_DIR"
