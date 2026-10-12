#!/usr/bin/env bash
# Queue full-sized Isaac jobs across task worktrees; each job may batch many lanes.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec 9>"${QLM_SCALEUP_GPU_LOCK:-/tmp/qlm-scaleup-gpu0.lock}"
flock 9
exec "${script_dir}/run60.sh" "$@"
