"""Part 2 environment: Go2 walks on three legs while one forelimb tracks a curve.

Paper Sec. IV-B. Random rational Bézier curves are sampled around the robot, the
episode lasts 20 s, the policy runs at 50 Hz and sees a 15-step history of
proprioception plus the foot command.
"""

from __future__ import annotations

import math

from mjlab.envs import ManagerBasedRlEnvCfg
from mjlab.envs import mdp as envs_mdp
from mjlab.envs.mdp import dr
from mjlab.managers.event_manager import EventTermCfg
from mjlab.managers.observation_manager import ObservationGroupCfg, ObservationTermCfg
from mjlab.managers.reward_manager import RewardTermCfg
from mjlab.managers.scene_entity_config import SceneEntityCfg
from mjlab.managers.termination_manager import TerminationTermCfg
from mjlab.scene import SceneCfg
from mjlab.sensor import ContactMatch, ContactSensorCfg
from mjlab.sim import MujocoCfg, SimulationCfg
from mjlab.tasks.velocity import mdp as vel_mdp
from mjlab.terrains import TerrainEntityCfg
from mjlab.utils.noise import UniformNoiseCfg as Unoise
from mjlab.viewer import ViewerConfig

from leg_manip.assets.go2 import (
    BASE_BODY,
    FOOT_GEOM_NAMES,
    GO2_ACTION_SCALE,
    MANIP_CALF_BODIES,
    get_go2_robot_cfg,
)
from leg_manip.tasks.track.mdp import observations as obs_mdp
from leg_manip.tasks.track.mdp import rewards as rew_mdp
from leg_manip.tasks.track.mdp.actions import FilteredJointPositionActionCfg
from leg_manip.tasks.track.mdp.commands import FootTrajectoryCommandCfg
from leg_manip.tasks.track.mdp.events import apply_manip_foot_force

CMD = "foot_traj"
HISTORY = 15
FEET_SENSOR = "feet_ground_contact"
BODY_SENSOR = "body_ground_contact"
SELF_SENSOR = "self_collision"


def make_track_env_cfg(play: bool = False) -> ManagerBasedRlEnvCfg:
    feet_ground = ContactSensorCfg(
        name=FEET_SENSOR,
        primary=ContactMatch(mode="geom", pattern=FOOT_GEOM_NAMES, entity="robot"),
        secondary=ContactMatch(mode="body", pattern="terrain"),
        fields=("found", "force"),
        reduce="netforce",
        num_slots=1,
        track_air_time=True,
    )
    body_ground = ContactSensorCfg(
        name=BODY_SENSOR,
        primary=ContactMatch(
            mode="geom",
            entity="robot",
            pattern=(
                "base_collision",
                "head_collision",
                "head_lower_collision",
                ".*_thigh_collision",
            ),
        ),
        secondary=ContactMatch(mode="body", pattern="terrain"),
        fields=("found", "force"),
        reduce="none",
        num_slots=1,
        history_length=4,
    )
    self_collision = ContactSensorCfg(
        name=SELF_SENSOR,
        primary=ContactMatch(mode="subtree", pattern=BASE_BODY, entity="robot"),
        secondary=ContactMatch(mode="subtree", pattern=BASE_BODY, entity="robot"),
        fields=("found", "force"),
        reduce="none",
        num_slots=1,
        history_length=4,
    )

    ##
    # Observations. Actor: 15-step history of [gravity, q, qd, a_{t-1}, command].
    ##

    actor_terms = {
        "projected_gravity": ObservationTermCfg(
            func=envs_mdp.projected_gravity, noise=Unoise(n_min=-0.05, n_max=0.05)
        ),
        "joint_pos": ObservationTermCfg(
            func=envs_mdp.joint_pos_rel,
            params={"biased": True},
            noise=Unoise(n_min=-0.01, n_max=0.01),
        ),
        "joint_vel": ObservationTermCfg(
            func=envs_mdp.joint_vel_rel, noise=Unoise(n_min=-1.5, n_max=1.5)
        ),
        "actions": ObservationTermCfg(func=envs_mdp.last_action),
        "command": ObservationTermCfg(
            func=envs_mdp.generated_commands, params={"command_name": CMD}
        ),
    }
    critic_terms = {
        "projected_gravity": ObservationTermCfg(func=envs_mdp.projected_gravity),
        "joint_pos": ObservationTermCfg(func=envs_mdp.joint_pos_rel),
        "joint_vel": ObservationTermCfg(func=envs_mdp.joint_vel_rel),
        "actions": ObservationTermCfg(func=envs_mdp.last_action),
        "command": ObservationTermCfg(
            func=envs_mdp.generated_commands, params={"command_name": CMD}
        ),
        "base_lin_vel": ObservationTermCfg(func=envs_mdp.base_lin_vel),
        "base_ang_vel": ObservationTermCfg(func=envs_mdp.base_ang_vel),
        "ee_pos": ObservationTermCfg(
            func=obs_mdp.ee_pos_heading, params={"command_name": CMD}
        ),
        "ee_dir": ObservationTermCfg(
            func=obs_mdp.ee_dir_heading, params={"command_name": CMD}
        ),
        "ee_error": ObservationTermCfg(
            func=obs_mdp.ee_pos_error_heading, params={"command_name": CMD}
        ),
        "phase": ObservationTermCfg(
            func=obs_mdp.traj_phase, params={"command_name": CMD}
        ),
        "foot_contact": ObservationTermCfg(
            func=vel_mdp.foot_contact, params={"sensor_name": FEET_SENSOR}
        ),
    }
    # Targets of the concurrent state estimator (Ji et al. 2022): base velocity and
    # manipulating foot position. Only the estimator loss reads this group.
    estimator_terms = {
        "base_lin_vel": ObservationTermCfg(func=envs_mdp.base_lin_vel),
        "ee_pos": ObservationTermCfg(
            func=obs_mdp.ee_pos_heading, params={"command_name": CMD}
        ),
    }
    observations = {
        "actor": ObservationGroupCfg(
            terms=actor_terms, enable_corruption=not play, history_length=HISTORY
        ),
        "critic": ObservationGroupCfg(terms=critic_terms, enable_corruption=False),
        "estimator_target": ObservationGroupCfg(
            terms=estimator_terms, enable_corruption=False
        ),
    }

    actions = {
        "joint_pos": FilteredJointPositionActionCfg(
            entity_name="robot",
            actuator_names=(".*",),
            scale=GO2_ACTION_SCALE,
            use_default_offset=True,
            cutoff_hz=10.0,
        )
    }

    commands = {
        CMD: FootTrajectoryCommandCfg(
            entity_name="robot",
            # One curve per 20 s episode, as in the paper.
            resampling_time_range=(1e9, 1e9),
            debug_vis=True,
        )
    }

    calf_cfg = SceneEntityCfg(
        "robot", body_names=MANIP_CALF_BODIES, preserve_order=True
    )
    events = {
        "reset_base": EventTermCfg(
            func=envs_mdp.reset_root_state_uniform,
            mode="reset",
            params={
                "pose_range": {
                    "x": (-0.5, 0.5),
                    "y": (-0.5, 0.5),
                    "z": (0.0, 0.03),
                    "yaw": (-math.pi, math.pi),
                },
                "velocity_range": {},
            },
        ),
        "reset_robot_joints": EventTermCfg(
            func=envs_mdp.reset_joints_by_offset,
            mode="reset",
            params={
                "position_range": (-0.1, 0.1),
                "velocity_range": (0.0, 0.0),
                "asset_cfg": SceneEntityCfg("robot", joint_names=(".*",)),
            },
        ),
        "push_robot": EventTermCfg(
            func=envs_mdp.push_by_setting_velocity,
            mode="interval",
            interval_range_s=(4.0, 8.0),
            params={"velocity_range": {"x": (-0.4, 0.4), "y": (-0.4, 0.4)}},
        ),
        # "The end-effector can handle unknown forces attached to it."
        "ee_force": EventTermCfg(
            func=apply_manip_foot_force,
            mode="step",
            params={
                "asset_cfg": calf_cfg,
                "command_name": CMD,
                "force_range": (-15.0, 15.0),
                "duration_s": (0.5, 3.0),
                "cooldown_s": (1.0, 5.0),
            },
        ),
        # Domain randomization (ranges from the paper's LaTeX comments, adapted).
        "foot_friction": EventTermCfg(
            mode="startup",
            func=dr.geom_friction,
            params={
                "asset_cfg": SceneEntityCfg("robot", geom_names=FOOT_GEOM_NAMES),
                "operation": "abs",
                "axes": [0],
                "ranges": (0.5, 1.25),
                "shared_random": True,
            },
        ),
        "base_mass": EventTermCfg(
            mode="startup",
            func=dr.body_mass,
            params={
                "asset_cfg": SceneEntityCfg("robot", body_names=(BASE_BODY,)),
                "operation": "scale",
                "ranges": (0.8, 1.2),
            },
        ),
        "base_com": EventTermCfg(
            mode="startup",
            func=dr.body_com_offset,
            params={
                "asset_cfg": SceneEntityCfg("robot", body_names=(BASE_BODY,)),
                "operation": "add",
                "ranges": {0: (-0.05, 0.05), 1: (-0.03, 0.03), 2: (-0.03, 0.03)},
            },
        ),
        "pd_gains": EventTermCfg(
            mode="startup",
            func=dr.pd_gains,
            params={
                "asset_cfg": SceneEntityCfg("robot", actuator_names=[".*"]),
                "kp_range": (0.8, 1.2),
                "kd_range": (0.8, 1.2),
                "operation": "scale",
            },
        ),
        "encoder_bias": EventTermCfg(
            mode="startup",
            func=dr.encoder_bias,
            params={"asset_cfg": SceneEntityCfg("robot"), "bias_range": (-0.01, 0.01)},
        ),
    }

    # Weights: tracking terms from paper Table I; stability terms from the table rows
    # commented out in the LaTeX source. Deviations, found in local runs: the paper's
    # sigmas are not given, and with 0.25 the far targets (up to 2 m) gave no signal;
    # the action smoothing terms (-0.3 in the comments) made early episodes so
    # costly that the policy learned to fall immediately, so they are reduced and a
    # termination penalty is added. Expect to tune these on the training server.
    rewards = {
        "ee_pos_xy": RewardTermCfg(
            func=rew_mdp.track_ee_pos_xy,
            weight=0.8,
            params={"command_name": CMD, "std": 0.5},
        ),
        "ee_pos_z": RewardTermCfg(
            func=rew_mdp.track_ee_pos_z,
            weight=0.8,
            params={"command_name": CMD, "std": 0.5, "z_scale": 5.0},
        ),
        "ee_dir": RewardTermCfg(
            func=rew_mdp.track_ee_dir,
            weight=0.3,
            params={"command_name": CMD, "sigma": 0.5},
        ),
        "ee_acc": RewardTermCfg(
            func=rew_mdp.ee_velocity_change, weight=-5.0, params={"command_name": CMD}
        ),
        "base_acc": RewardTermCfg(func=rew_mdp.base_velocity_change, weight=-5.0),
        "base_orientation": RewardTermCfg(
            func=envs_mdp.flat_orientation_l2, weight=-5.0
        ),
        "self_collision": RewardTermCfg(
            func=vel_mdp.self_collision_cost,
            weight=-5.0,
            params={"sensor_name": SELF_SENSOR},
        ),
        "joint_pos_limits": RewardTermCfg(func=envs_mdp.joint_pos_limits, weight=-10.0),
        "torque_limits": RewardTermCfg(
            func=rew_mdp.torque_limit_violation, weight=-1.0
        ),
        "free_gait": RewardTermCfg(
            func=rew_mdp.free_gait,
            weight=2.0,
            params={"command_name": CMD, "sensor_name": FEET_SENSOR},
        ),
        "joint_torques": RewardTermCfg(func=envs_mdp.joint_torques_l2, weight=-1e-4),
        "joint_deviation": RewardTermCfg(func=rew_mdp.joint_deviation_l2, weight=-1e-4),
        "joint_vel": RewardTermCfg(func=envs_mdp.joint_vel_l2, weight=-1e-4),
        "joint_acc": RewardTermCfg(func=envs_mdp.joint_acc_l2, weight=-2.5e-7),
        "action_rate": RewardTermCfg(func=envs_mdp.action_rate_l2, weight=-0.01),
        "action_acc": RewardTermCfg(func=envs_mdp.action_acc_l2, weight=-0.01),
        "termination": RewardTermCfg(func=envs_mdp.is_terminated, weight=-200.0),
    }

    terminations = {
        "time_out": TerminationTermCfg(func=envs_mdp.time_out, time_out=True),
        "fell_over": TerminationTermCfg(
            func=envs_mdp.bad_orientation, params={"limit_angle": math.radians(70.0)}
        ),
        "body_contact": TerminationTermCfg(
            func=vel_mdp.illegal_contact, params={"sensor_name": BODY_SENSOR}
        ),
    }

    cfg = ManagerBasedRlEnvCfg(
        scene=SceneCfg(
            terrain=TerrainEntityCfg(terrain_type="plane"),
            entities={"robot": get_go2_robot_cfg()},
            sensors=(feet_ground, body_ground, self_collision),
            num_envs=1,
            extent=2.0,
        ),
        observations=observations,
        actions=actions,
        commands=commands,
        events=events,
        rewards=rewards,
        terminations=terminations,
        viewer=ViewerConfig(
            origin_type=ViewerConfig.OriginType.ASSET_BODY,
            entity_name="robot",
            body_name=BASE_BODY,
            distance=2.0,
            elevation=-15.0,
            azimuth=90.0,
        ),
        sim=SimulationCfg(
            nconmax=None,
            njmax=300,
            contact_sensor_maxmatch=64,
            mujoco=MujocoCfg(
                timestep=0.005,
                iterations=10,
                ls_iterations=20,
                ccd_iterations=50,
                impratio=10,
                cone="elliptic",
            ),
        ),
        decimation=4,
        episode_length_s=20.0,
    )

    if play:
        cfg.events.pop("push_robot", None)
        cfg.events.pop("ee_force", None)
    return cfg
