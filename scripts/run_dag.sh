#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

readonly DAG=cartpulse_daily
readonly ATTEMPTS=60

airflow() {
    docker compose --profile airflow exec -T airflow airflow "$@"
}

# Print how many runs are active and how many failed, as "active failed".
count_runs() {
    airflow dags list-runs "${DAG}" --output json 2>/dev/null | python3 -c '
import json
import sys

runs = json.load(sys.stdin)
active = sum(run["state"] in ("queued", "running") for run in runs)
failed = sum(run["state"] == "failed" for run in runs)
print(active, failed)
'
}

# The scheduler runs the DAG, as it does in normal use. `airflow dags test` would race it.
airflow dags trigger "${DAG}" > /dev/null

for ((attempt = 1; attempt <= ATTEMPTS; attempt++)); do
    read -r active failed < <(count_runs)
    if [[ "${failed}" -gt 0 ]]; then
        echo "${DAG} has ${failed} failed run(s)." >&2
        exit 1
    fi
    if [[ "${active}" -eq 0 ]]; then
        echo "All ${DAG} runs succeeded."
        exit 0
    fi
    sleep 5
done

echo "${DAG} was still running after ${ATTEMPTS} checks." >&2
exit 1
