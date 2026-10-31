#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

# A separate Compose project gets its own containers and volumes, and these variables win
# over .env, so the tests erase nothing but their own temporary databases.
export COMPOSE_PROJECT_NAME=cartpulse-test
export MYSQL_ROOT_PASSWORD=test-only
export MYSQL_PASSWORD=test-only
export MONGO_ROOT_PASSWORD=test-only
export POSTGRES_PASSWORD=test-only
export MYSQL_PORT=13306
export MONGO_PORT=37017
export POSTGRES_PORT=15434
export CARTPULSE_TEST_STACK=1

# Cleaning up would otherwise take down a run that is still going.
if [[ -n "$(docker compose ps --quiet)" ]]; then
    echo "The ${COMPOSE_PROJECT_NAME} stack is already running. Wait for that run to finish." >&2
    exit 1
fi

remove_stack() {
    local status=$?
    if [[ "${status}" -ne 0 ]]; then
        docker compose logs --tail 40
    fi
    docker compose down --volumes --remove-orphans
}
trap remove_stack EXIT

bash scripts/download_data.sh
docker compose up --detach --wait mysql mongo postgres
uv run pytest -m integration "$@"
