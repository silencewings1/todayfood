#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT=${PROJECT_ROOT:-$(dirname "$SCRIPT_DIR")}
RETENTION_DAYS=${RETENTION_DAYS:-14}
STAMP=$(date +%F)
BACKUP_ROOT="$PROJECT_ROOT/backups"
DAY_DIR="$BACKUP_ROOT/$STAMP"
LOG_DIR="$PROJECT_ROOT/logs"
DB_PATH="$PROJECT_ROOT/backend/data/log.db"

if [ ! -f "$DB_PATH" ]; then
  echo "Database not found: $DB_PATH" >&2
  exit 1
fi

mkdir -p "$DAY_DIR"

if [ -d "$LOG_DIR" ]; then
  tar -czf "$DAY_DIR/logs-$STAMP.tar.gz" -C "$LOG_DIR" .
fi

if [ -f "$DB_PATH" ]; then
  if command -v sqlite3 >/dev/null 2>&1; then
    sqlite3 "$DB_PATH" ".backup '$DAY_DIR/log-$STAMP.db'"
  else
    cp "$DB_PATH" "$DAY_DIR/log-$STAMP.db"
    [ -f "$DB_PATH-wal" ] && cp "$DB_PATH-wal" "$DAY_DIR/log-$STAMP.db-wal"
    [ -f "$DB_PATH-shm" ] && cp "$DB_PATH-shm" "$DAY_DIR/log-$STAMP.db-shm"
  fi
fi

find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d -mtime +"$RETENTION_DAYS" -exec rm -rf {} +
