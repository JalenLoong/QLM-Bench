"""Three-view evaluation media; consumes existing hooks and never owns physics."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image


class RGBVideo:
    def __init__(self, path, ffmpeg, ffprobe, fps):
        self.path = Path(path)
        self.partial = self.path.with_suffix('.partial.mp4')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists() or self.partial.exists():
            raise FileExistsError(self.path)
        self.ffprobe, self.fps, self.count = ffprobe, fps, 0
        self.command = [ffmpeg, '-hide_banner', '-loglevel', 'error', '-f', 'rawvideo',
            '-pix_fmt', 'rgb24', '-s', '1280x720', '-framerate', str(fps), '-i', 'pipe:0',
            '-vf', 'scale=in_range=full:out_range=tv:out_color_matrix=bt709',
            '-c:v', 'libx264', '-threads', '2', '-preset', 'veryfast', '-crf', '20',
            '-pix_fmt', 'yuv420p', '-color_range', 'tv', '-color_primaries', 'bt709',
            '-color_trc', 'bt709', '-colorspace', 'bt709', '-movflags', '+faststart', str(self.partial)]
        self.errors = self.path.with_suffix('.encoder.log').open('x')
        self.process = subprocess.Popen(self.command, stdin=subprocess.PIPE, stderr=self.errors)
        self.closed = False

    def write(self, rgb):
        if self.closed or rgb.shape != (720, 1280, 3) or rgb.dtype != np.uint8:
            raise ValueError('Open RGB8 1280x720 stream required')
        self.process.stdin.write(np.ascontiguousarray(rgb).tobytes())
        self.count += 1

    def close(self):
        if self.closed:
            raise ValueError('Video sink was already finalized')
        self.closed = True
        self.process.stdin.close()
        code = self.process.wait(timeout=120)
        self.errors.close()
        if code or self.count == 0:
            raise RuntimeError('RGB encoder failed or received no physical frame: ' + str(self.partial))
        raw = subprocess.check_output([self.ffprobe, '-v', 'error', '-select_streams', 'v:0',
            '-count_frames', '-show_entries', 'stream=width,height,nb_read_frames,r_frame_rate',
            '-of', 'json', str(self.partial)], text=True)
        stream = json.loads(raw)['streams'][0]
        if (stream['width'], stream['height'], int(stream['nb_read_frames'])) != (1280, 720, self.count):
            raise ValueError('Encoded RGB video does not preserve the captured frame membership')
        self.partial.replace(self.path)
        return {'path': str(self.path), 'frames': self.count, 'fps': self.fps,
                'width': 1280, 'height': 720, 'input': 'actual RGB uint8',
                'encoding': 'H264/yuv420p/CRF20/veryfast', 'validation': 'all frames decoded by ffprobe',
                'ffprobe': stream, 'command': self.command}


def create_observer(profile):
    """The already reviewed monitor camera; constructed only after AppLauncher."""
    import omni.replicator.core as rep
    geometry = profile['observer']
    camera = rep.create.camera(position=geometry['position'], look_at=geometry['look_at'], focal_length=24)
    product = rep.create.render_product(camera, (1280, 720))
    rgb = rep.AnnotatorRegistry.get_annotator('rgb', device='cpu')
    rgb.attach(product)
    return rgb, (camera, product)


class EvaluationVideoRecorder:
    """Record every trial, including failures, on authoritative simulation boundaries."""
    def __init__(self, env, observer, output, ffmpeg, ffprobe):
        self.env, self.observer = env, observer
        self.output, self.ffmpeg, self.ffprobe = Path(output), ffmpeg, ffprobe
        self.active = False
        self.sinks = {}
        self.last_tick = None
        self.directory = None

    def begin(self, trial_id):
        if self.active or self.env.episode_tick != 0:
            raise ValueError('Video begins only after an explicit episode reset')
        self.directory = self.output / trial_id
        self.directory.mkdir(parents=True, exist_ok=False)
        self.sinks = {role: RGBVideo(self.directory / (role + '.mp4'), self.ffmpeg, self.ffprobe,
                                   25 if role == 'observer' else 50)
                      for role in ('ego', 'task_centric', 'observer')}
        self.index = (self.directory / 'frames.jsonl').open('x')
        self.epoch = self.env.episode_clock.reset_epoch
        self.last_tick = None
        self.terminal = None
        self.max_box_progress_x_m = 0.
        self.active = True
        self.capture()
        statistics = {}
        for role in ('ego', 'task_centric', 'observer'):
            image = self.last_images[role]
            statistics[role] = {'std': float(image.std()), 'min': int(image.min()), 'max': int(image.max())}
            Image.fromarray(image).save(self.directory / ('initial_' + role + '.png'))
        (self.directory / 'initial_visual_gate.json').write_text(json.dumps(statistics, indent=2) + '\n')
        if any(row['std'] < 1 for row in statistics.values()):
            raise RuntimeError('Initial approved-scene RGB is essentially uniform; rendering gate failed')

    def capture(self, *, terminal=False):
        if not self.active:
            return
        tick = self.env.episode_tick
        if self.env.episode_clock.reset_epoch != self.epoch:
            raise ValueError('Post-reset frames cannot enter the previous trial video')
        duplicate = tick == self.last_tick
        self.max_box_progress_x_m = max(self.max_box_progress_x_m,
            float(self.env.geometric_center[0, 0]) - self.env._initial_center_x)
        images = {}
        for role, sensor in [('ego', self.env.front_camera), ('task_centric', self.env.task_camera)]:
            image = sensor.data.output['rgb'].torch[0].detach().cpu().numpy().copy()
            images[role] = image
            if not duplicate:
                self.sinks[role].write(image)
                self._index(role, tick, sensor_frame_id=int(sensor.frame.torch[0]))
        if (tick % 20 == 0 and not duplicate) or terminal:
            image = np.asarray(self.observer.get_data())[:, :, :3].copy()
            images['observer'] = image
            # A terminal at the ordinary observer grid was already recorded above.
            if not duplicate or tick % 20 != 0:
                self.sinks['observer'].write(image)
                self._index('observer', tick, sensor_frame_id=None)
        if terminal:
            for role, image in images.items():
                Image.fromarray(image).save(self.directory / ('terminal_' + role + '.png'))
        self.last_images = images
        if 'observer' in images and float(images['observer'].std()) < 1:
            raise RuntimeError('Fixed observer lost scene content; suspected RTX memory-pressure failure')
        self.last_tick = tick

    def _index(self, role, tick, sensor_frame_id):
        self.index.write(json.dumps({'role': role, 'frame_index': self.sinks[role].count - 1,
            'physics_step': tick, 'simulation_time_ns': self.env.simulation_time_ns,
            'reset_epoch': self.epoch, 'sensor_frame_id': sensor_frame_id}) + '\n')
        self.index.flush()

    def submit(self, prepared):
        pass

    def before_control(self, action):
        pass

    def after_physics(self, force, torque):
        pass

    def after_control(self):
        if self.active and self.env.episode_tick % 10 == 0:
            self.capture()

    def before_reset(self, ids):
        if not self.active:
            return
        owned = self.env.terminal_snapshot
        if owned is None or owned['reset_epoch'] != self.epoch:
            raise ValueError('Owned terminal-before-reset evidence required')
        self.capture(terminal=True)
        self.terminal = {'physics_step': owned['physics_step'],
            'simulation_time_ns': owned['simulation_time_ns'], 'reset_epoch': self.epoch,
            'reason': owned['reason'], 'captured_before_reset': True,
            'evaluator_state': copy.deepcopy(owned['state']), 'task_review': copy.deepcopy(owned['task_review']),
            'rgb_hashes': copy.deepcopy(owned['rgb_hashes'])}
        self.active = False

    def close_trial(self, *, error=None):
        self.active = False
        self.index.close()
        videos = {role: sink.close() for role, sink in self.sinks.items()}
        record = {'schema': 'qlm-evaluation-media-v1', 'reset_epoch': self.epoch,
                  'terminal': self.terminal, 'videos': videos, 'error': error,
                  'max_box_progress_x_m': self.max_box_progress_x_m,
                  'timeline': 'simulation time; model waits do not add frames',
                  'observer_model_input': False}
        (self.directory / 'media.json').write_text(json.dumps(record, indent=2, allow_nan=False) + '\n')
        self.sinks = {}
        return record
