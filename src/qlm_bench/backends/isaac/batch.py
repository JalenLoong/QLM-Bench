"""Opt-in same-task vector capacity probe; launch Isaac only on explicit invocation."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import time
from qlm_bench.tasks.registration import load_registration, SCALEUP_TASK_IDS


def main(argv=None):
    import sys
    raw = list(sys.argv[1:] if argv is None else argv)
    p = argparse.ArgumentParser(prog='qlm collect-batch')
    p.add_argument('--task', choices=SCALEUP_TASK_IDS, required=True)
    p.add_argument('--num-envs', type=int, required=True)
    p.add_argument('--profile', type=Path, required=True)
    p.add_argument('--resource-root', type=Path, required=True)
    p.add_argument('--simulation-seconds', type=float, default=4.)
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--observer', action='store_true', help='Include one1280x720 diagnostic observer per lane at25Hz')
    p.add_argument('--debug-last-frame', type=Path, help='Optional temporary RGB contact sheet for a failed capacity probe')
    p.add_argument('--probe-only', action='store_true', required=True,
                   help='Short runtime/render capacity probe; no demonstration artifacts')
    if '--help' in raw or '-h' in raw:
        p.print_help(); return 0
    from isaaclab.app import AppLauncher
    from rambo.utils.physx import validate_rambo_visualizer_args
    AppLauncher.add_app_launcher_args(p)
    args = p.parse_args(raw)
    validate_rambo_visualizer_args(p, args, raw)
    if args.num_envs < 1 or args.simulation_seconds <= 0 or args.simulation_seconds > 30:
        p.error('Positive environments and bounded0..30 simulation seconds required')
    registration = load_registration(args.task, ready=True)
    if not registration.get('batch_environment') or not registration.get('batch_expert'):
        p.error('Task batch environment/expert plug-ins are not implemented')
    args.enable_cameras = True
    app = runtime = None
    code = 1
    try:
        app = AppLauncher(args)
        import torch
        import numpy as np
        from rambo.tasks.common.batch_controller_runtime import BatchControllerRuntime
        from rambo.contracts_v2.runtime import prepare_command
        start = time.monotonic()
        runtime = BatchControllerRuntime(registration['gym_id'], num_envs=args.num_envs,
            profile=json.loads(args.profile.read_text()), resource_root=args.resource_root,
            seed=args.seed, episode_length_s=args.simulation_seconds,
            device=getattr(args, 'device', 'cuda:0'))
        env = runtime.base_env
        observers = []
        if args.observer:
            import omni.replicator.core as rep
            geometry = runtime.cfg.approved_profile['observer']
            for index in range(args.num_envs):
                offset = env._terrain.env_origins[index].cpu().numpy()
                camera = rep.create.camera(position=(np.asarray(geometry['position']) + offset).tolist(),
                    look_at=(np.asarray(geometry['look_at']) + offset).tolist(), focal_length=24)
                product = rep.create.render_product(camera, (1280, 720))
                rgb = rep.AnnotatorRegistry.get_annotator('rgb', device='cpu'); rgb.attach(product)
                observers.append((camera, product, rgb))
            for _ in range(4):
                env.sim.render()
        runtime.prime_render()
        startup_s = time.monotonic() - start
        origin = env._terrain.env_origins
        assert torch.allclose(env.base_pos_w[:, :2], origin[:, :2], atol=1e-4)
        assert env.front_camera.data.output['rgb'].torch.shape[0] == args.num_envs
        assert env.task_camera.data.output['rgb'].torch.shape[0] == args.num_envs
        step_start = time.monotonic()
        commands_per_lane = [0] * args.num_envs
        frames_per_lane = [0] * args.num_envs
        rgb_valid = [True] * args.num_envs
        rgb_stats = [{} for _ in range(args.num_envs)]
        last_pixels = [{} for _ in range(args.num_envs)]
        torch.cuda.reset_peak_memory_stats()
        for tick in range(round(args.simulation_seconds * 50)):
            experts = runtime.expert_commands()
            prepared = [prepare_command(request, f'lane-{i}:{tick}', env.lane_tick(i)) if request is not None else None
                        for i, (request, _) in enumerate(experts)]
            results = runtime.step(prepared)
            states = runtime.state()
            if observers and tick % 2 == 0:
                for _, _, annotator in observers:
                    pixels = np.asarray(annotator.get_data())
                    if pixels.shape[:2] != (720, 1280):
                        raise ValueError('Observer did not produce its declared image')
            for index, (request, _) in enumerate(experts):
                if request is None:
                    continue
                commands_per_lane[index] += 1
                snapshot = results[index]['terminal'] or states[index]
                current_valid = True
                for role, pixels in snapshot['rgb'].items():
                    pixels = np.asarray(pixels)
                    if pixels.shape != (720, 1280, 3) or pixels.dtype != np.uint8:
                        raise ValueError('Invalid RGB shape/dtype')
                    std = float(pixels.std())
                    stats = rgb_stats[index].setdefault(role, dict(first_std=std, last_std=std, low_variation_frames=0))
                    stats['last_std'] = std
                    stats['low_variation_frames'] += int(std <= 3)
                    current_valid &= std > 3
                    last_pixels[index][role] = pixels[:, :, :3].copy()
                # This short user-requested capacity test permits renderer warmup;
                # formal collection still validates its own initial capture.
                rgb_valid[index] = current_valid
                frames_per_lane[index] += 1
            if not any(env.lane_active):
                break
        torch.cuda.synchronize()
        elapsed = time.monotonic() - step_start
        passed = all(n > 0 for n in commands_per_lane) and all(rgb_valid) and torch.isfinite(env.base_pos_w).all().item()
        if args.debug_last_frame is not None:
            from PIL import Image, ImageDraw
            sheet = Image.new('RGB', (384, args.num_envs * 128), 'white'); draw = ImageDraw.Draw(sheet)
            for index, views in enumerate(last_pixels):
                draw.text((2, index * 128), f'lane {index}', fill='black')
                for column, role in enumerate(('ego', 'task_centric')):
                    sheet.paste(Image.fromarray(views[role]).resize((192,108)), (column*192,index*128+16))
            args.debug_last_frame.parent.mkdir(parents=True, exist_ok=True)
            sheet.save(args.debug_last_frame)
        report = dict(probe_only=True, artifact_retention=False, task=args.task, num_envs=args.num_envs,
                      policy_cameras=2 * args.num_envs, observer_cameras=len(observers),
                      passed=passed, commands_per_lane=commands_per_lane, frames_per_lane=frames_per_lane,
                      rgb_statistics=rgb_stats,
                      startup_seconds=startup_s, run_wall_seconds=elapsed,
                      aggregate_commands_per_wall_second=sum(commands_per_lane) / elapsed,
                      torch_peak_allocated_GiB=torch.cuda.max_memory_allocated() / 2**30,
                      torch_peak_reserved_GiB=torch.cuda.max_memory_reserved() / 2**30)
        print('QLM_BATCH_PROBE_RESULT=' + json.dumps(report, allow_nan=False), flush=True)
        code = 0 if passed else 1
    finally:
        if runtime is not None:
            runtime.close()
        if app is not None:
            app.app.close(exit_code=code)
    return code
