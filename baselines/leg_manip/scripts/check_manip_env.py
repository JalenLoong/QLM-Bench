"""Smoke check of the manipulation tasks: scene, head depth camera, point cloud.

For each task: build the env, step a few times with zero actions, extract the
object point cloud and check that its points lie on the object (object frame).

    uv run python scripts/check_manip_env.py [--num-envs 16]
"""

from __future__ import annotations

import argparse

import mjlab  # noqa: F401  (configures Warp and mujoco GL before use)
import torch
from mjlab.envs import ManagerBasedRlEnv

from leg_manip.tasks.manip.env_cfg import make_manip_env_cfg
from leg_manip.tasks.manip.perception import object_point_cloud, robot_state
from leg_manip.tasks.manip.specs import TASKS
from leg_manip.traj import inverse_yaw_transform


def check(name: str, num_envs: int, device: str) -> bool:
    spec = TASKS[name]
    cfg = make_manip_env_cfg(spec)
    cfg.scene.num_envs = num_envs
    env = ManagerBasedRlEnv(cfg=cfg, device=device)
    env.reset()
    zero = torch.zeros(num_envs, env.action_manager.total_action_dim, device=device)
    for _ in range(5):
        env.step(zero)
    cmd = env.command_manager.get_term("foot_traj")
    cloud, num_valid = object_point_cloud(env)
    ids = torch.arange(num_envs, device=device)
    pos, yaw = cmd.object_pose(ids)
    local = inverse_yaw_transform(cloud + env.scene.env_origins.unsqueeze(1), yaw, pos)
    visible = num_valid > 0
    lo = local[visible].reshape(-1, 3).amin(0).tolist()
    hi = local[visible].reshape(-1, 3).amax(0).tolist()
    state = robot_state(env)
    print(f"[{name}] envs with object in view: {int(visible.sum())}/{num_envs}")
    print(f"  object pixels per env: {num_valid.tolist()}")
    print(
        "  cloud bbox in object frame: "
        + " ".join(f"{a}[{lo[i]:.2f},{hi[i]:.2f}]" for i, a in enumerate("xyz"))
    )
    print(
        f"  cloud {tuple(cloud.shape)}, state {tuple(state.shape)}, "
        f"command {tuple(cmd.command.shape)}"
    )
    # The object occupies x in [-0.06, 0.5], |y| < 0.31, z in [0, 0.5] in its frame
    # (door open adds up to -0.4 in x).
    ok = bool(visible.float().mean() >= 0.8) and lo[0] > -0.5 and hi[2] < 0.6
    print(f"  {'PASS' if ok else 'FAIL'}")
    env.close()
    return ok


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-envs", type=int, default=16)
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    results = [check(name, args.num_envs, args.device) for name in TASKS]
    raise SystemExit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
