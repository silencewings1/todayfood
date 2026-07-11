#!/usr/bin/env bash
set -euo pipefail

umask 022

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$PROJECT_DIR/frontend"
DEPLOY_DIR="$FRONTEND_DIR/.deploy"
RELEASES_DIR="$DEPLOY_DIR/releases"
CURRENT_LINK="$DEPLOY_DIR/current"
LOCK_FILE="/home/ospacer/.local/state/snowflow-site-deploy.lock"
KEEP_RELEASES=5

mkdir -p "$(dirname "$LOCK_FILE")" "$RELEASES_DIR"
exec 9>"$LOCK_FILE"
flock -n 9 || { echo "Another snowflow-site deployment is running" >&2; exit 1; }

switch_release() {
  local target="$1"
  ln -sfn "$target" "$DEPLOY_DIR/current.next"
  mv -Tf "$DEPLOY_DIR/current.next" "$CURRENT_LINK"
}

smoke_test() {
  local response
  response="$(curl --fail --silent --show-error --location --max-time 15 https://snowflow.cloud/projects/todayfood/)"
  [[ "$response" == *'<html'* ]]
  response="$(curl --fail --silent --show-error --max-time 15 https://snowflow.cloud/projects/todayfood/health)"
  [[ "$response" == *'"status"'* ]]
}

case "${1:-}" in
  --list)
    current="$(readlink -f "$CURRENT_LINK" 2>/dev/null || true)"
    for release in "$RELEASES_DIR"/*; do
      [ -d "$release" ] || continue
      [ "$release" = "$current" ] && marker='*' || marker=' '
      printf '%s %s\n' "$marker" "$(basename "$release")"
    done
    exit 0
    ;;
  --rollback)
    target="$RELEASES_DIR/${2:?Provide a release id}"
    [ -s "$target/index.html" ] || { echo "Release not found: $2" >&2; exit 1; }
    previous="$(readlink -f "$CURRENT_LINK" 2>/dev/null || true)"
    switch_release "$target"
    smoke_test || { [ -n "$previous" ] && switch_release "$previous"; exit 1; }
    printf 'TodayFood frontend rolled back to %s\n' "$2"
    exit 0
    ;;
  "") ;;
  *) echo "Usage: $0 [--list|--rollback release-id]" >&2; exit 2 ;;
esac

cd "$FRONTEND_DIR"
release_id="$(date -u +%Y%m%dT%H%M%S)-$(date -u +%N)-$(git -C "$PROJECT_DIR" rev-parse --short HEAD)"
release_dir="$RELEASES_DIR/$release_id"
previous="$(readlink -f "$CURRENT_LINK" 2>/dev/null || true)"
switched=false

cleanup() {
  local status=$?
  trap - EXIT INT TERM
  if [ "$status" -ne 0 ]; then
    if [ "$switched" = true ] && [ -n "$previous" ] && [ -s "$previous/index.html" ]; then
      switch_release "$previous"
      smoke_test || true
    fi
    if [ "$(readlink -f "$CURRENT_LINK" 2>/dev/null || true)" != "$release_dir" ]; then
      rm -rf "$release_dir"
    fi
  fi
  exit "$status"
}
trap cleanup EXIT INT TERM

npm ci
npm run build -- --outDir "$release_dir" --emptyOutDir
[ -s "$release_dir/index.html" ] || { echo "Missing index.html" >&2; exit 1; }
find "$release_dir/assets" -type f -print -quit | grep -q . || { echo "Missing frontend assets" >&2; exit 1; }
grep -q '/projects/todayfood/assets/' "$release_dir/index.html" || { echo "Incorrect Vite base path" >&2; exit 1; }
chmod -R a+rX "$release_dir"

switch_release "$release_dir"
switched=true
smoke_test
switched=false

current="$(readlink -f "$CURRENT_LINK")"
find "$RELEASES_DIR" -mindepth 1 -maxdepth 1 -type d -printf '%T@ %p\n' | sort -nr | cut -d' ' -f2- \
  | while IFS= read -r release; do [ "$release" = "$current" ] || printf '%s\n' "$release"; done \
  | tail -n "+$KEEP_RELEASES" | xargs -r rm -rf --

trap - EXIT INT TERM
printf 'TodayFood frontend release active: %s\n' "$release_id"
