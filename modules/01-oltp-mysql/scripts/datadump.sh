#!/usr/bin/env bash
set -euo pipefail

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly MODULE_DIR
readonly TARGET="${MODULE_DIR}/data/sales_data.sql"

cd "${MODULE_DIR}/../.."

# --single-transaction reads a consistent snapshot without locking writers out of the table.
# Dump to a temp file first so a failed run never replaces a good backup.
docker compose exec -T mysql sh -c \
    'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysqldump --user=root --single-transaction sales sales_data' \
    > "${TARGET}.part"
mv "${TARGET}.part" "${TARGET}"

echo "Dumped sales_data to: ${TARGET}"
