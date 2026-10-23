#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: deploy-frontend.sh <staging-dir> <html-dir>" >&2
  exit 2
fi

STAGING_DIR=${1%/}
HTML_DIR=${2%/}
DIST_DIR="$STAGING_DIR/frontend/dist"

if [[ -z "$STAGING_DIR" || -z "$HTML_DIR" || "$HTML_DIR" == "/" ]]; then
  echo "Staging and document directories must be non-root paths." >&2
  exit 2
fi
if [[ ! -f "$DIST_DIR/index.html" ]]; then
  echo "Staged frontend build not found: $DIST_DIR/index.html" >&2
  exit 1
fi

mkdir -p -- "$HTML_DIR"
find "$HTML_DIR" -mindepth 1 -maxdepth 1 ! -name '50x.html' -exec rm -rf -- {} +
find "$DIST_DIR" -mindepth 1 -maxdepth 1 ! -name '50x.html' -exec cp -a -- {} "$HTML_DIR/" \;

case "$STAGING_DIR" in
  /tmp/kkoi-frontend-deploy-*) rm -rf -- "$STAGING_DIR" ;;
esac

echo "Frontend deployed to $HTML_DIR"
