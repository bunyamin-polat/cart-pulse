#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../../.."

# --drop keeps the load idempotent: the documents have no _id, so a plain re-run would duplicate them.
docker compose exec -T mongo sh -c \
    'mongoimport --username root --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin \
        --db catalog --collection electronics --drop --file /import/catalog.json'

# createIndex is a no-op when the index already exists.
docker compose exec -T mongo sh -c \
    'mongosh --quiet --username root --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin \
        catalog --eval "db.electronics.createIndex({ type: 1 })"'
