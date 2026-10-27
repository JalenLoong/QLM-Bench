"""Manipulation task environments: the tracking environment plus an articulated
object, a head depth camera and an expert (or planner-driven) foot trajectory."""

from __future__ import annotations

from mjlab.entity import EntityCfg
from mjlab.envs import ManagerBasedRlEnvCfg
from mjlab.managers.event_manager import EventTermCfg
from mjlab.managers.recorder_manager import RecorderTermCfg
from mjlab.sensor import CameraSensorCfg

from leg_manip.assets.objects import OBJECT_GEOM_GROUP
from leg_manip.tasks.manip.mdp import (
    ExpertTrajectoryCommandCfg,
    reset_robot_and_object,
    trajectory_command_observation,
)
from leg_manip.tasks.manip.recording import OBJECT_JOINT_RECORDER, ObjectJointRecorder
from leg_manip.tasks.manip.specs import ManipTaskSpec
from leg_manip.tasks.track.env_cfg import CMD, make_track_env_cfg

CAMERA = "head_depth"

# The head depth camera is defined in the Go2 MJCF (camera "head_depth" on the
# bracket body), with its pose taken from the project's CAD assembly: 0.32 m ahead
# of and 0.33 m above the base origin, pitched 30.5 deg down, depth FOV 87 x 58 deg,
# rendered at 160 x 100. See src/leg_manip/assets/go2/CAMERA_MOUNT.md.
CAMERA_SIZE = (160, 100)


def make_manip_env_cfg(
    spec: ManipTaskSpec, planner: bool = False
) -> ManagerBasedRlEnvCfg:
    """Args:
    spec: task definition.
    planner: if True the foot trajectory is not sampled from the expert; the
        caller pushes planner predictions in every 0.1 s (closed-loop evaluation).
    """
    cfg = make_track_env_cfg(play=True)
    cfg.scene.entities["object"] = EntityCfg(spec_fn=spec.object_spec_fn)
    cfg.scene.sensors = (cfg.scene.sensors or ()) + (
        CameraSensorCfg(
            name=CAMERA,
            camera_name=f"robot/{CAMERA}",
            width=CAMERA_SIZE[0],
            height=CAMERA_SIZE[1],
            data_types=("depth", "segmentation"),
            enabled_geom_groups=(0, OBJECT_GEOM_GROUP, 2),
            use_textures=False,
        ),
    )
    cfg.commands[CMD] = ExpertTrajectoryCommandCfg(
        entity_name="robot",
        resampling_time_range=(1e9, 1e9),
        debug_vis=True,
        object_name="object",
        expert_vector=spec.expert_vector,
        duration_s=spec.duration_s,
        sample_on_reset=not planner,
    )
    cfg.observations["actor"].terms["command"].func = trajectory_command_observation
    cfg.recorders[OBJECT_JOINT_RECORDER] = RecorderTermCfg(func=ObjectJointRecorder)
    cfg.events.pop("reset_base", None)
    cfg.events["reset_robot_and_object"] = EventTermCfg(
        func=reset_robot_and_object,
        mode="reset",
        params={
            "distance_range": spec.distance_range,
            "bearing_range_deg": spec.bearing_range_deg,
            "object_yaw_range_deg": spec.object_yaw_range_deg,
            "object_joint_range": spec.object_joint_range,
        },
    )
    # Paper: 200 planner steps at 10 Hz per demonstration.
    cfg.episode_length_s = 20.0
    cfg.scene.env_spacing = 6.0
    return cfg
