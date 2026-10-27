import subprocess
import sys

# The planner must import on the AMD cluster, where mjlab / mujoco_warp / warp are
# not installed. Block them and import every planner-side module.
CODE = """
import importlib
import pkgutil
import sys
for name in (
    "mjlab", "mujoco", "mujoco_warp", "warp", "pytorch3d",
    "leg_manip.tasks", "leg_manip.collect", "leg_manip.controller",
):
    sys.modules[name] = None
import leg_manip.planner
for module in pkgutil.walk_packages(
    leg_manip.planner.__path__, leg_manip.planner.__name__ + "."
):
    importlib.import_module(module.name)
import leg_manip.hub
import leg_manip.demo_io
import leg_manip.traj
print("ok")
"""


def test_planner_imports_without_simulator():
    out = subprocess.run(
        [sys.executable, "-c", CODE], capture_output=True, text=True, check=False
    )
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "ok"
