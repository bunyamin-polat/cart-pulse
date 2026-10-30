#!/usr/bin/env bash
set -euo pipefail

readonly BASE_URL="https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBM-DB0321EN-SkillsNetwork/Bigdata%20and%20Spark"
DATA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../data" && pwd)"
readonly DATA_DIR

download() {
    local target="${DATA_DIR}/$1"

    if [[ -s "${target}" ]]; then
        echo "Already downloaded: ${target}"
        return
    fi

    # Download to a temp file first so an interrupted transfer never looks like a complete one.
    curl --fail --silent --show-error --location --output "${target}.part" "${BASE_URL}/$1"
    mv "${target}.part" "${target}"
    echo "Downloaded: ${target}"
}

download "searchterms.csv"
download "model.tar.gz"

# macOS tar treats ._* files as metadata and fails on them. Only a checksum is skipped here.
if [[ ! -d "${DATA_DIR}/sales_prediction.model" ]]; then
    tar -xzf "${DATA_DIR}/model.tar.gz" -C "${DATA_DIR}" --exclude '._*'
    echo "Extracted: ${DATA_DIR}/sales_prediction.model"
fi
