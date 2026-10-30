#!/usr/bin/env bash
set -euo pipefail

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly MODULE_DIR
readonly TARGET="${MODULE_DIR}/data/electronics.csv"

cd "${MODULE_DIR}/../.."

# Write to a temp file first so a failed run never replaces a good export.
docker compose exec -T mongo sh -c \
    'mongoexport --username root --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin \
        --db catalog --collection electronics --type=csv --fields _id,type,model' \
    > "${TARGET}.part"
mv "${TARGET}.part" "${TARGET}"

echo "Exported catalog to: ${TARGET}"
