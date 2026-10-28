#!/usr/bin/env bash
# Create or reuse the Leg-Manip planner venv on the MI355X cluster.
#
# The venv borrows ROCm torch (and every other package) from an existing cluster
# environment through a .pth file and installs only what is missing, pinned by
# constraints.txt. The existing environment is never modified.
#
#   LEGMANIP_BASE_PYTHON=/shared/yue/wamx/env/v3m/bin/python \
#   LEGMANIP_VENV=/shared/$USER/legmanip/env/legmanip-amd \
#   bash scripts/amd/setup_env.sh <project dir>
set -euo pipefail

project=$(cd "${1:-.}" && pwd)
base=${LEGMANIP_BASE_PYTHON:?set LEGMANIP_BASE_PYTHON to a python with ROCm torch}
venv=${LEGMANIP_VENV:?set LEGMANIP_VENV}
constraints=$project/scripts/amd/constraints.txt
stamp=$venv/.legmanip-setup

key=$(
  {
    echo "$base"
    cat "$constraints" "$project/pyproject.toml"
  } | sha256sum | cut -d' ' -f1
)
if [[ -f $stamp && $(cat "$stamp") == "$key" ]] &&
  "$venv/bin/python" -c "import leg_manip.planner.cluster" 2>/dev/null; then
  echo "[setup] reusing $venv"
  exit 0
fi

"$base" - <<'EOF'
import sys
import torch
print("[setup] base python", sys.version.split()[0], "torch", torch.__version__,
      "hip", torch.version.hip)
EOF
base_paths=$("$base" -c 'import sysconfig as s; p = s.get_paths()
print(p["purelib"]); print(p["platlib"])' | sort -u)

rm -rf "$venv"
mkdir -p "$(dirname "$venv")"
"$base" -m venv --without-pip "$venv"
site=$("$venv/bin/python" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')
echo "$base_paths" >"$site/_legmanip_base_env.pth"

pip_args=(install --disable-pip-version-check --no-input -c "$constraints" -e "$project")
if "$base" -m pip --python "$venv/bin/python" --version >/dev/null 2>&1; then
  echo "[setup] installing with the base environment's pip"
  "$base" -m pip --python "$venv/bin/python" "${pip_args[@]}"
elif command -v uv >/dev/null 2>&1; then
  # uv ignores the .pth packages, so every pinned dependency lands in the venv.
  echo "[setup] base has no usable pip; installing with uv"
  uv pip install --python "$venv/bin/python" -c "$constraints" -e "$project"
elif "$venv/bin/python" -c "import ensurepip" 2>/dev/null; then
  echo "[setup] base has no usable pip; bootstrapping pip in the venv"
  "$venv/bin/python" -m ensurepip --default-pip
  "$venv/bin/python" -m pip "${pip_args[@]}"
else
  # Debian/Ubuntu system pythons ship without ensurepip: use the pip zipapp.
  echo "[setup] base has no usable pip and no ensurepip; using pip.pyz"
  pyz=$venv/pip.pyz
  "$base" -c 'import sys, urllib.request
urllib.request.urlretrieve("https://bootstrap.pypa.io/pip/pip.pyz", sys.argv[1])' "$pyz"
  "$base" "$pyz" --python "$venv/bin/python" "${pip_args[@]}"
fi

"$venv/bin/python" - <<'EOF'
import importlib.metadata as m
import torch
import leg_manip.planner.cluster  # noqa: F401  (imports train, dataset, DP3, hub)
names = ("numpy", "zarr", "diffusers", "huggingface_hub", "wandb", "tyro", "leg-manip")
print("[setup] venv torch", torch.__version__, "hip", torch.version.hip,
      {n: m.version(n) for n in names})
EOF
echo "$key" >"$stamp"
echo "[setup] ready $venv"
