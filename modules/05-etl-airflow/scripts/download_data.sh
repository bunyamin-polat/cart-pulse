#!/usr/bin/env bash
set -euo pipefail

readonly BASE_URL="https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud"
DATA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../data" && pwd)"
readonly DATA_DIR

download() {
    local url="$1"
    local target="${DATA_DIR}/$2"

    if [[ -s "${target}" ]]; then
        echo "Already downloaded: ${target}"
        return
    fi

    # Download to a temp file first so an interrupted transfer never looks like a complete one.
    curl --fail --silent --show-error --location --output "${target}.part" "${url}"
    mv "${target}.part" "${target}"
    echo "Downloaded: ${target}"
}

download "${BASE_URL}/IBM-DB0321EN-SkillsNetwork/ETL/sales.sql" "sales.sql"
download "${BASE_URL}/sales-csv3mo8i5SHvta76u7DzUfhiw.csv" "sales.csv"
