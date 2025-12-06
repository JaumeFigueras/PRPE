#!/usr/bin/env bash
# Save Renfe realtime JSON to /tmp/remfe using the project's Python virtual environment.
# - Assumes the Python virtual environment is located at /home/prpe/.venv
# - Runs src/apps/import/import_realtime_renfe.py
#
# Usage:
#   ./save_renfe_json.sh [URL]
# If URL is not provided, defaults to Renfe vehicle positions endpoint.

set -euo pipefail

# Config
VENV_PY="/home/prpe/soft/PRPE/.venv/bin/python"
TARGET_DIR="/home/prpe/data/gtfs"
DEFAULT_URL="https://ssl.renfe.com/ftransit/Fichero_CER_FOMENTO/fomento_transit.zip"
REPO_ROOT="/home/prpe/soft/PRPE"

# Path to the import script relative to repo root
IMPORT_SCRIPT="${REPO_ROOT}/src/apps/imports/import_gtfs_renfe.py"

# URL argument or default
URL="${1:-$DEFAULT_URL}"

# Checks
if [[ ! -x "$VENV_PY" ]]; then
  echo "Error: Python interpreter not found at '${VENV_PY}'. Ensure the virtualenv exists." >&2
  exit 1
fi

if [[ ! -f "$IMPORT_SCRIPT" ]]; then
  echo "Error: Import script not found at '${IMPORT_SCRIPT}'." >&2
  exit 1
fi

# Ensure target directory exists
mkdir -p "$TARGET_DIR"

# Optional: set a log file in /tmp (rotating handled by script when -l is used)
LOG_FILE="/home/prpe/logs/gtfs_renfe.log"

# Execute the import script
# -u URL
# -d directory to save (timestamped file will be created inside)
# -a attempts (optional; default 5). You can tweak if needed.
# -l log file (optional)
"$VENV_PY" "$IMPORT_SCRIPT" \
  -u "$URL" \
  -d "$TARGET_DIR" \
  -a 3 \
  -l "$LOG_FILE"

echo "JSON saved under directory: $TARGET_DIR"
echo "Log written to: $LOG_FILE"