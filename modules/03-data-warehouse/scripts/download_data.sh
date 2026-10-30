#!/usr/bin/env bash
set -euo pipefail

readonly BASE_URL="https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud"
readonly FILES=(
    "nm75oOK5n7AGME1F7_OIQg/CREATE-SCRIPT.sql"
    "IBM-DB0321EN-SkillsNetwork/datawarehousing/data/DimDate.csv"
    "IBM-DB0321EN-SkillsNetwork/datawarehousing/DimCategory.csv"
    "IBM-DB0321EN-SkillsNetwork/datawarehousing/DimCountry.csv"
    "IBM-DB0321EN-SkillsNetwork/datawarehousing/FactSales.csv"
)
DATA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../data" && pwd)"
readonly DATA_DIR

for file in "${FILES[@]}"; do
    target="${DATA_DIR}/$(basename "${file}")"

    if [[ -s "${target}" ]]; then
        echo "Already downloaded: ${target}"
        continue
    fi

    # Download to a temp file first so an interrupted transfer never looks like a complete one.
    curl --fail --silent --show-error --location --output "${target}.part" "${BASE_URL}/${file}"
    mv "${target}.part" "${target}"
    echo "Downloaded: ${target}"
done
