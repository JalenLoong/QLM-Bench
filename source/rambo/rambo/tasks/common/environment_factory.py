"""Shared environment construction for collection, evaluation and teleoperation.

Importing the factory is safe outside Isaac.  Runtime imports occur only when
creating a configuration or an environment after AppLauncher has started Kit.
"""
from __future__ import annotations

from typing import Any
from pathlib import Path
import hashlib

LIFT_BASKET_TASK_ID = 'Isaac-RAMBO-Quadruped-Lift-Basket-Go2-v0'
PUSH_BOX_TASK_ID = 'Isaac-RAMBO-Quadruped-Push-Box-V2-Go2-v0'
PRESS_BUTTON_TASK_ID = 'Isaac-RAMBO-Quadruped-Press-Button-V2-Go2-v0'
TASK_IDS = (PUSH_BOX_TASK_ID, LIFT_BASKET_TASK_ID, PRESS_BUTTON_TASK_ID)


def resolve_task_asset(profile: dict, resource_root: str | Path,
                       asset_id: str | None = None) -> Path:
    """Resolve the exact reviewed source identity through the public registry."""
    from qlm_bench.assets import load_registry, load_manifest, resolve_asset

    expected = profile['asset_sha256']
    if asset_id is None:
        asset_id = profile.get('asset_id')
    if asset_id is None:
        matches = []
        for resource in load_registry()['resources']:
            manifest = load_manifest(resource['asset_id'])
            if manifest['files'][manifest['entrypoint']]['sha256'] == expected:
                matches.append(resource['asset_id'])
        if len(matches) != 1:
            raise ValueError('Task asset identity must resolve to one registry entry')
        asset_id = matches[0]
    manifest = load_manifest(asset_id)
    if manifest['files'][manifest['entrypoint']]['sha256'] != expected:
        raise ValueError('Resolved task asset differs from the reviewed task profile')
    for relative, digest in profile.get('asset_bundle_sha256', {}).items():
        if relative in manifest['files']:
            if manifest['files'][relative]['sha256'] != digest:
                raise ValueError('Resolved task resource inventory differs from the reviewed task profile')
        elif relative.startswith('textures/') or relative.endswith(('.usd', '.usda', '.usdc', '.mdl')):
            raise ValueError('Reviewed task resource is missing from the runtime inventory')
        # Historical conversion/provenance JSON remains source metadata, not
        # an implicit runtime cache dependency.
    asset = resolve_asset(asset_id, resource_root)
    if hashlib.sha256(asset.read_bytes()).hexdigest() != expected:
        raise ValueError('Resolved task asset differs from the reviewed task profile')
    return asset


def configure_environment(cfg: Any, *, task_id: str, seed: int,
                          episode_length_s: float, view: str = 'third-person',
                          camera_setup: str | None = None) -> None:
    """Apply the accepted deterministic runtime settings without changing physics."""
    cfg.seed = seed
    cfg.events = None
    cfg.obs_noise = False
    cfg.randomize_episode_progress = False
    cfg.randomize_initial_state = False
    cfg.enable_sampled_velocity_commands = False
    cfg.enable_sampled_pos_commands = False
    cfg.enable_sampled_force_commands = False
    cfg.episode_length_s = episode_length_s
    for sequence in cfg.contact_generator_config['contact_sequence'].values():
        horizon = sum(float(segment[1]) for segment in sequence)
        if horizon < episode_length_s + 1.0:
            sequence[-1][1] += episode_length_s + 1.0 - horizon
    cfg.scene.env_spacing = 10.0
    cfg.viewer.eye = [-1.6, -2.0, 1.10]
    cfg.viewer.lookat = [0.70, 0.10, 0.28]
    cfg.viewer.origin_type = 'world'
    cfg.viewer.asset_name = None
    if view == 'ego':
        cfg.enable_rgb_camera = True
    if task_id == LIFT_BASKET_TASK_ID:
        cfg.terminate_on_limb_contact = False
    if camera_setup == 'robot-dual-v3':
        from rambo.tasks.common.lift_camera_rig import configure
        configure(cfg, camera_setup)


def make_config(task_id: str, *, seed: int, episode_length_s: float,
                view: str = 'third-person', camera_setup: str | None = None,
                **runtime_options: Any) -> Any:
    from rambo.utils.registry import parse_env_cfg

    cfg = parse_env_cfg(task_id, num_envs=1, **runtime_options)
    configure_environment(cfg, task_id=task_id, seed=seed,
                          episode_length_s=episode_length_s, view=view,
                          camera_setup=camera_setup)
    return cfg


def make_collection_config(task_id: str, *, seed: int, max_actions: int,
                           profile: dict, asset_path: str,
                           device: str = 'cuda:0') -> Any:
    from rambo.utils.physx import configure_physx

    cfg = make_config(task_id, seed=seed, episode_length_s=24.,
                      camera_setup='robot-dual-v3', device=device, use_fabric=True)
    configure_physx(cfg)
    cfg.sim.render_interval = 10
    cfg.front_camera.update_period = .02
    cfg.task_camera.update_period = .02
    cfg.terminate_on_body_contact = False
    cfg.terminate_on_limb_contact = False
    cfg.terminate_on_undesired_foot_contact = False
    cfg.approved_asset_path = asset_path
    cfg.approved_profile = profile
    cfg.pilot_max_physics_steps = max_actions * 10
    return cfg


def make_environment(cfg: Any, *, task_id: str | None = None,
                     environment_type: Any = None, wrapper: bool = True) -> Any:
    """Create the same environment for any action provider.

    ``environment_type`` supports existing explicit task constructors while
    registrations migrate.  Consumers normally provide the public task ID.
    """
    if environment_type is not None:
        env = environment_type(cfg)
    else:
        if task_id is None:
            raise ValueError('Environment construction requires a task ID or type')
        import gymnasium as gym
        import rambo
        rambo.register_tasks()
        env = gym.make(task_id, cfg=cfg)
    if wrapper:
        from rambo.rl import Crl2VecEnvWrapper
        return Crl2VecEnvWrapper(env)
    return env


def make_task_config(task_id: str, *, profile: dict, resource_root: str | Path,
                     seed: int = 42, episode_length_s: float = 24.,
                     view: str = 'third-person', asset_id: str | None = None,
                     device: str = 'cuda:0', use_fabric: bool = True) -> Any:
    """Construct the reviewed nominal task for any action provider."""
    import copy
    import math
    if task_id not in TASK_IDS:
        raise ValueError('Only the three current native9 tasks are supported')
    if not math.isfinite(episode_length_s) or episode_length_s <= 0 or not math.isclose(episode_length_s*50,round(episode_length_s*50)):
        raise ValueError('Episode horizon must contain whole 50 Hz command intervals')
    profile = copy.deepcopy(profile)
    asset = resolve_task_asset(profile, resource_root, asset_id)
    cfg = make_config(task_id, seed=seed, episode_length_s=episode_length_s,
                      view=view, camera_setup='robot-dual-v3', device=device,
                      use_fabric=use_fabric)
    from rambo.utils.physx import configure_physx
    configure_physx(cfg)
    cfg.sim.render_interval = 10
    cfg.front_camera.update_period = cfg.task_camera.update_period = .02
    cfg.approved_profile = profile
    cfg.approved_asset_path = str(asset)
    cfg.pilot_max_physics_steps = round(episode_length_s*500)
    if task_id == PUSH_BOX_TASK_ID:
        import numpy as np
        from rambo.tasks.direct.rambo_quadruped.push_box_v2 import asset_geometry
        from rambo.tasks.common.push_box_geometry import source_geometry
        low,high = asset_geometry(asset)
        center = (low+high)/2
        geometry = source_geometry(low,high)
        cfg.primary_position = (profile['initial_face_distance_x']+geometry['dimensions'][0]/2-float(center[0]),
                                float(cfg.ee_default_command[1])-float(center[1]),
                                profile['initial_floor_clearance']-float(low[2]))
        cfg.primary_orientation = (0.,0.,0.,1.)
    elif task_id == LIFT_BASKET_TASK_ID:
        from rambo.assets import BASKET_INITIAL_ORIENTATION_XYZW
        cfg.primary_position = tuple(profile['primary_position'])
        cfg.primary_orientation = BASKET_INITIAL_ORIENTATION_XYZW
    else:
        cfg.primary_position = tuple(profile['asset_origin_xyz'])
        cfg.primary_orientation = (0.,0.,0.,1.)
    return cfg
