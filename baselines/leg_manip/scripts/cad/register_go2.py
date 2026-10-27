"""Register the CAD Go2 to the MJCF base frame and report the camera mount pose.

    python scripts/cad/step_inspect.py <assembly.step> verts.npz
    uv run python scripts/cad/register_go2.py verts.npz

The CAD frame has +z up and -y forward (all four knees lie on the +y side of their
feet, and Go2's knees point backwards), so base axes map as x -> -y, y -> +x,
z -> +z. The translation is found by ICP between the CAD trunk and the MJCF base
visual meshes. Prints the bracket extents and the camera mount face in the base
frame. See src/leg_manip/assets/go2/CAMERA_MOUNT.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

import mujoco
import numpy as np
from scipy.spatial import cKDTree

GO2_XML = Path(__file__).resolve().parents[2] / "src/leg_manip/assets/go2/go2.xml"
# CAD columns are the images of the base axes.
R = np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]], dtype=float)


def base_mesh_points() -> np.ndarray:
    m = mujoco.MjModel.from_xml_path(str(GO2_XML))
    base = m.body("base").id
    out = []
    for g in range(m.ngeom):
        if m.geom_bodyid[g] != base or m.geom_type[g] != mujoco.mjtGeom.mjGEOM_MESH:
            continue
        mid = m.geom_dataid[g]
        v = m.mesh_vert[m.mesh_vertadr[mid] : m.mesh_vertadr[mid] + m.mesh_vertnum[mid]]
        rot = np.zeros(9)
        mujoco.mju_quat2Mat(rot, m.geom_quat[g])
        out.append(v @ rot.reshape(3, 3).T + m.geom_pos[g])
    return np.concatenate(out)


def main() -> None:
    d = np.load(sys.argv[1])
    go2 = d["go2机器狗"] / 1000.0
    bracket = d["单支架"] / 1000.0
    trunk = go2[go2[:, 2] > 1.397 - 0.03]
    src = base_mesh_points()
    src = src[src[:, 2] > -0.03] @ R.T
    tree = cKDTree(trunk)
    zmin = go2[:, 2].min()
    feet = go2[go2[:, 2] < zmin + 0.025]
    t = np.array([np.median(go2[:, 0]), feet[:, 1].mean(), 1.397])
    for _ in range(40):
        dist, idx = tree.query(src + t)
        keep = dist < np.percentile(dist, 80)
        t = t + (trunk[idx[keep]] - (src[keep] + t)).mean(0)
    dist, _ = tree.query(src + t)
    print(
        f"base origin in CAD root frame (m): {t.round(4)}, median residual "
        f"{np.median(dist) * 1000:.1f} mm"
    )
    q = (bracket - t) @ R
    print(f"bracket in base frame: min {q.min(0).round(3)} max {q.max(0).round(3)}")
    mount = q[(q[:, 2] >= 0.30) & (q[:, 0] >= 0.26)]
    print(
        f"camera mount in base frame: min {mount.min(0).round(3)} "
        f"max {mount.max(0).round(3)}"
    )


if __name__ == "__main__":
    main()
