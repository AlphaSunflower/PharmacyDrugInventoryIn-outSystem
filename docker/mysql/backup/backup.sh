#!/bin/bash
set -euo pipefail

BACKUP_DIR="/backups"
MYSQL_HOST="${MYSQL_HOST:-mysql}"
MYSQL_DATABASE="${MYSQL_DATABASE:-pharmacy_db}"

mkdir -p "$BACKUP_DIR"

run_backup() {
  local timestamp
  local backup_day
  local temp_file
  local final_file

  timestamp="$(date +%Y-%m-%d_%H-%M-%S)"
  backup_day="$(date +%Y-%m-%d)"
  temp_file="$BACKUP_DIR/.pharmacy_db_${timestamp}.sql.tmp"
  final_file="$BACKUP_DIR/pharmacy_db_${timestamp}.sql"

  export MYSQL_PWD="$MYSQL_ROOT_PASSWORD"
  if mysqldump \
      --host="$MYSQL_HOST" \
      --user=root \
      --single-transaction \
      --quick \
      --lock-tables=false \
      --default-character-set=utf8mb4 \
      --set-gtid-purged=OFF \
      "$MYSQL_DATABASE" > "$temp_file"; then
    mv "$temp_file" "$final_file"
    unset MYSQL_PWD

    find "$BACKUP_DIR" -maxdepth 1 -type f -name 'pharmacy_db_*.sql' | while read -r old_file; do
      old_day="$(basename "$old_file" | sed -E 's/^pharmacy_db_([0-9]{4}-[0-9]{2}-[0-9]{2})_.*/\1/')"
      if [[ "$old_day" < "$backup_day" ]]; then
        rm -f "$old_file"
      fi
    done
    echo "Backup completed: $final_file"
  else
    unset MYSQL_PWD
    rm -f "$temp_file"
    echo "Backup failed at $(date '+%Y-%m-%d %H:%M:%S')" >&2
  fi
}

run_backup

while true; do
  next_midnight="$(date -d 'tomorrow 00:00' +%s)"
  now="$(date +%s)"
  sleep "$((next_midnight - now))"
  run_backup
done
