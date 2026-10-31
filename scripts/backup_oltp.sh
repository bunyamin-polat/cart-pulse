#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

readonly BACKUP_DIR="data/backups"
TARGET="${BACKUP_DIR}/orders_$(date -u +%Y%m%dT%H%M%SZ).sql"
readonly TARGET
mkdir -p "${BACKUP_DIR}"

# --single-transaction reads a consistent snapshot without locking writers out of the table.
# Dump to a temp file first so a failed run never leaves a partial backup behind.
docker compose exec -T mysql sh -c \
    'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysqldump --user=root --single-transaction "$MYSQL_DATABASE" orders' \
    > "${TARGET}.part"
mv "${TARGET}.part" "${TARGET}"

echo "Backup written to: ${TARGET}"
