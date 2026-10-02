#!/usr/bin/env bash
# Prepare an independent CPU-only data environment without changing Isaac/Torch.
set -euo pipefail
readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
readonly DATA_ENV="${QLM_DATA_VENV:-${REPO_ROOT}/.venv-data}"
readonly DATA_INTERPRETER="${QLM_DATA_PYTHON:-python3.10}"
readonly UV_COMMAND="${UV_BIN:-uv}"
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    cat <<'EOF'
Usage: bash scripts/setup_qlm_data.sh
Environment:
  QLM_DATA_VENV    Independent destination (default: this repo/.venv-data)
  QLM_DATA_PYTHON  Existing Python 3.10, 3.11 or 3.12 interpreter (default python3.10)
  UV_BIN          uv command (default uv)

Install only four pinned CPU data dependencies and this QLM package. ffmpeg and
ffprobe are separately supplied executables. No WAM, simulator or Torch install.
EOF
    exit 0
fi
if [[ "$#" -ne 0 ]]; then
    echo "Unknown setup argument; use --help." >&2
    exit 64
fi
if [[ ! -x "${DATA_ENV}/bin/python" ]]; then
    "${UV_COMMAND}" venv --python "${DATA_INTERPRETER}" "${DATA_ENV}"
fi
readonly DATA_PYTHON="${DATA_ENV}/bin/python"
"${DATA_PYTHON}" - <<'PY'
import sys
from importlib.util import find_spec
if not ((3, 10) <= sys.version_info[:2] < (3, 13)):
    raise SystemExit("The pinned CPU data lock supports Python 3.10–3.12")
if any(find_spec(name) is not None for name in ('torch', 'isaacsim', 'isaaclab', 'wam_policy')):
    raise SystemExit("Choose a separate CPU data environment; existing model/simulator environments are not modified")
PY
"${UV_COMMAND}" pip install --python "${DATA_PYTHON}" --no-deps -r "${REPO_ROOT}/requirements/qlm-data-tools.lock"
"${UV_COMMAND}" pip install --python "${DATA_PYTHON}" --no-deps --editable "${REPO_ROOT}"
"${DATA_PYTHON}" - <<'PY'
from importlib.metadata import version
import sys
from qlm_bench.data.tools import convert_raw
from qlm_bench.compatibility.dataset_v2 import conversion, conversion_lift, merge
for package in ("numpy", "pillow", "pyarrow", "av"):
    print(package + "=" + version(package))
assert not any(name.split('.')[0] in {'torch', 'rambo', 'isaaclab', 'isaacsim', 'transformers', 'diffusers', 'wam_policy'} for name in sys.modules)
print("Independent CPU QLM conversion/merge imports passed")
PY
echo "Use --data-python ${DATA_PYTHON} for qlm collect."
