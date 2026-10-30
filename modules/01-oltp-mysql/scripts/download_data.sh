#!/usr/bin/env bash
set -euo pipefail

readonly DATA_URL="https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBM-DB0321EN-SkillsNetwork/oltp/oltpdata.csv"
DATA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../data" && pwd)"
readonly DATA_DIR
readonly TARGET="${DATA_DIR}/oltpdata.csv"

if [[ -s "${TARGET}" ]]; then
    echo "Already downloaded: ${TARGET}"
    exit 0
fi

# Download to a temp file first so an interrupted transfer never looks like a complete one.
curl --fail --silent --show-error --location --output "${TARGET}.part" "${DATA_URL}"
mv "${TARGET}.part" "${TARGET}"
echo "Downloaded: ${TARGET}"
