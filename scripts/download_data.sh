#!/usr/bin/env bash
set -euo pipefail

readonly BASE_URL="https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBM-DB0321EN-SkillsNetwork"
DATA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/data/raw"
readonly DATA_DIR
mkdir -p "${DATA_DIR}"

download() {
    local target
    target="${DATA_DIR}/$(basename "$1")"

    if [[ -s "${target}" ]]; then
        echo "Already downloaded: $(basename "${target}")"
        return
    fi

    # Download to a temp file first so an interrupted transfer never looks like a complete one.
    curl --fail --silent --show-error --location --output "${target}.part" "${BASE_URL}/$1"
    mv "${target}.part" "${target}"
    echo "Downloaded: $(basename "${target}")"
}

download "datawarehousing/data/DimDate.csv"
download "datawarehousing/DimCategory.csv"
download "datawarehousing/DimCountry.csv"
download "datawarehousing/FactSales.csv"
download "nosql/catalog.json"
download "ETL/accesslog.txt"
download "Bigdata%20and%20Spark/searchterms.csv"
