#!/usr/bin/env bash
# Set RAMBO_VENV and QLM_RESOURCE_ROOT, or pass --resource-root explicitly.
set -euo pipefail
readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "${SCRIPT_DIR}/run60.sh" \
    "${SCRIPT_DIR}/teleop_loco_manip.py" \
    --task Isaac-RAMBO-Quadruped-Lift-Basket-Go2-v0 \
    --view task --viz kit "$@"
