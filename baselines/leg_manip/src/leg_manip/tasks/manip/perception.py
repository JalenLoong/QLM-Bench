"""Planner inputs: object point cloud from the head depth camera, and robot state.

Both are expressed in the env's local world frame (sim world minus env origin), the
frame in which the planner reads point clouds and predicts trajectory parameters.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import mujoco
import torch

from leg_manip.traj import quat_to_yaw

if TYPE_CHECKING:
    from mjlab.entity import Entity
    from mjlab.envs import ManagerBasedRlEnv
    from mjlab.sensor import CameraSensor

STATE_DIM = 17  # base pos (3), sin/cos yaw (2), joint pos (12)


def camera_points_world(
    env: ManagerBasedRlEnv, sensor_name: str, object_name: str
) -> tuple[torch.Tensor, torch.Tensor]:
    """Back-project the depth image to sim-world points.

    Returns:
        points: (N, H*W, 3) world points (garbage where invalid).
        valid: (N, H*W) True for pixels that hit a geom of `object_name`.
    """
    cam: CameraSensor = env.scene[sensor_name]
    obj: Entity = env.scene[object_name]
    data = cam.data
    assert data.depth is not None and data.segmentation is not None
    depth = data.depth[..., 0]  # (N, H, W), planar depth, 0 = no hit
    seg = data.segmentation  # (N, H, W, 2): object id, object type
    n, h, w = depth.shape

    obj_geoms = obj.indexing.geom_ids.to(seg.device)
    is_geom = seg[..., 1] == int(mujoco.mjtObj.mjOBJ_GEOM)
    valid = is_geom & torch.isin(seg[..., 0], obj_geoms) & (depth > 0)

    fovy = math.radians(float(env.sim.mj_model.cam_fovy[cam.camera_idx]))
    f = (h / 2) / math.tan(fovy / 2)
    rows = torch.arange(h, device=depth.device, dtype=depth.dtype) + 0.5
    cols = torch.arange(w, device=depth.device, dtype=depth.dtype) + 0.5
    v, uu = torch.meshgrid(rows, cols, indexing="ij")
    # MuJoCo camera frame: x right, y up, looking along -z. Image row 0 is the top.
    x_c = (uu - w / 2) / f * depth
    y_c = -(v - h / 2) / f * depth
    z_c = -depth
    p_c = torch.stack([x_c, y_c, z_c], dim=-1).view(n, h * w, 3)

    cam_pos = env.sim.data.cam_xpos[:, cam.camera_idx]  # (N, 3)
    cam_mat = env.sim.data.cam_xmat[:, cam.camera_idx].view(n, 3, 3)
    points = p_c @ cam_mat.transpose(1, 2) + cam_pos.unsqueeze(1)
    return points, valid.view(n, h * w)


def object_point_cloud(
    env: ManagerBasedRlEnv,
    sensor_name: str = "head_depth",
    object_name: str = "object",
    num_points: int = 768,
    max_candidates: int = 4096,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Object point cloud in the env frame, downsampled with farthest point sampling.

    Returns:
        cloud: (N, num_points, 3).
        num_valid: (N,) number of object pixels seen (0 = object not visible; the
            cloud is then all zeros).
    """
    points, valid = camera_points_world(env, sensor_name, object_name)
    points = points - env.scene.env_origins.unsqueeze(1)
    n = points.shape[0]
    num_valid = valid.sum(-1)

    # Random subset of valid pixels (invalid ones get -inf keys and sort last).
    keys = torch.rand(valid.shape, device=points.device).masked_fill(~valid, -1.0)
    k = min(max_candidates, valid.shape[1])
    order = keys.topk(k, dim=-1).indices
    cand = points.gather(1, order.unsqueeze(-1).expand(-1, -1, 3))
    cand_valid = valid.gather(1, order)
    # Pad invalid candidates with the first valid point so FPS never picks them
    # while unique points remain.
    first = cand[:, :1].expand_as(cand)
    cand = torch.where(cand_valid.unsqueeze(-1), cand, first)
    cloud = farthest_point_sample(cand, num_points)
    cloud = torch.where((num_valid > 0).view(n, 1, 1), cloud, torch.zeros_like(cloud))
    return cloud, num_valid


def farthest_point_sample(points: torch.Tensor, k: int) -> torch.Tensor:
    """Batched farthest point sampling, (B, P, 3) -> (B, k, 3). Starts at point 0."""
    b, p, _ = points.shape
    idx = torch.zeros(b, k, dtype=torch.long, device=points.device)
    dist = torch.full((b, p), float("inf"), device=points.device)
    cur = torch.zeros(b, dtype=torch.long, device=points.device)
    ar = torch.arange(b, device=points.device)
    for i in range(k):
        idx[:, i] = cur
        d = (points - points[ar, cur].unsqueeze(1)).square().sum(-1)
        dist = torch.minimum(dist, d)
        cur = dist.argmax(-1)
    return points.gather(1, idx.unsqueeze(-1).expand(-1, -1, 3))


def robot_state(env: ManagerBasedRlEnv, robot_name: str = "robot") -> torch.Tensor:
    """(N, 17): base position (env frame), sin/cos yaw, joint positions."""
    robot: Entity = env.scene[robot_name]
    pos = robot.data.root_link_pos_w - env.scene.env_origins
    yaw = quat_to_yaw(robot.data.root_link_quat_w)
    return torch.cat(
        [
            pos,
            torch.sin(yaw).unsqueeze(-1),
            torch.cos(yaw).unsqueeze(-1),
            robot.data.joint_pos,
        ],
        dim=-1,
    )
