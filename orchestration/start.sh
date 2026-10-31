#!/usr/bin/env bash
set -euo pipefail

# A pid file left in the volume by the last run would stop the API server from starting.
rm -f /opt/airflow/*.pid

exec airflow standalone
