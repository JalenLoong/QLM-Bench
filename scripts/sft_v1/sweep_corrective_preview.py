"""Review material for a few corrective sweep episodes (sft-v1/QLM-DATA-002): videos, a 1 s contact sheet, a side-by-side with the
production demonstration of the same scene from the same tick, and review.md. Read only on RUN and the base release; writes OUT only.

Per episode, OUT/<uid>/:
  ego.mp4, task_centric.mp4   copies of the rendered Canonical videos (640x360, 50 FPS, OSMesa)
  observer-640x360.mp4        the Raw observer view (1280x720, 25 FPS, diagnostic only) scaled to 640x360
  sheet.jpg                   task-centric every 1 s plus the first-contact and success frames (full size), ego below (half size);
                              takeover / first contact / success tiles framed blue / yellow / green
  compare.mp4, compare.jpg    task-centric, corrective episode (left) and the production demonstration from the same absolute tick
                              (right), with rollout time and block yaw on every frame; the sheet every 1 s
Usage: sweep_corrective_preview.py --run RUN --out OUT --ideal PREP/ideal/results --scenes 034 024 025 076
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

import av
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corrective_release import FFMPEG, NORMALIZER_OFFSET, NORMALIZER_SCALE, sha  # noqa: E402
from sweep_corrective_release import BASE, TASK, load_segments, uid_of  # noqa: E402

BLUE, YELLOW, GREEN = (40, 120, 255), (255, 210, 0), (40, 220, 90)


def state(npz):
    """Per-boundary block geometry, contact and time from a takeover / ideal record (row i = boundary i)."""
    with np.load(npz) as z:
        c = {k: i for i, k in enumerate(z['columns'])};p = z['privileged'];req = z['requested'].copy()
    g = lambda k: p[:, c[k]]
    cx = np.stack([g(f'corner{i}_x') for i in range(8)], 1)
    return {'t': g('tick') * .002, 'yaw': np.rad2deg(2 * np.arctan2(g('object_qz'), g('object_qw'))), 'contact': g('fl_object_contact') > 0,
            'x_hi_cm': (g('goal_x1') - cx.max(1)) * 100, 'x_lo_cm': (cx.min(1) - g('goal_x0')) * 100, 'requested': req}


def frames(path, start=0, stop=None):
    with av.open(str(path)) as c:
        for i, f in enumerate(c.decode(video=0)):
            if stop is not None and i >= stop:
                break
            if i >= start:
                yield f.to_image()


def label(im, text, colour=None, width=4):
    im = im.copy();d = ImageDraw.Draw(im)
    d.rectangle([0, 0, im.width, 15], fill=(0, 0, 0));d.text((4, 2), text, fill=(255, 255, 0))
    if colour:
        for k in range(width):
            d.rectangle([k, k, im.width - 1 - k, im.height - 1 - k], outline=colour)
    return im


def encode(path, size, fps, images):
    cmd = [str(FFMPEG), '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{size[0]}x{size[1]}', '-r', str(fps),
           '-i', '-', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', str(path)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for im in images:
        p.stdin.write(np.asarray(im.convert('RGB'), np.uint8).tobytes())
    p.stdin.close()
    if p.wait():
        raise RuntimeError(f'ffmpeg failed for {path}')


def grid(tiles, cols):
    w, h = tiles[0].size;rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * w, rows * h), (20, 20, 20))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * w, (i // cols) * h))
    return sheet


def one(run, out, ideal_dir, segment, base_index):
    uid = uid_of(segment);ep = run / 'episodes' / uid;target = out / uid;target.mkdir(parents=True, exist_ok=True)
    videos = {k: ep / f'canonical/videos/chunk-000/observation.images.{k}/episode_000000.mp4' for k in ('ego', 'task_centric')}
    for k, v in videos.items():
        shutil.copy2(v, target / f'{k}.mp4')
    subprocess.run([str(FFMPEG), '-hide_banner', '-loglevel', 'error', '-y', '-i', str(ep / 'raw' / uid / 'cameras/observer.mp4'), '-vf', 'scale=640:360',
                    '-c:v', 'libx264', '-crf', '23', '-pix_fmt', 'yuv420p', str(target / 'observer-640x360.mp4')], check=True)
    s = state(run / 'takeover/results' / f"{segment['segment_id']}.npz")
    n = len(s['requested']);t0 = segment['takeover_s'];yaw0 = s['yaw'][0]
    first = int(np.flatnonzero(s['contact'])[0]) if s['contact'].any() else None
    low, high = NORMALIZER_OFFSET - NORMALIZER_SCALE, NORMALIZER_OFFSET + NORMALIZER_SCALE
    oor = ((s['requested'][:, :6] < low) | (s['requested'][:, :6] > high)).any(1)
    # ---- contact sheet
    marks = {0: ('takeover', BLUE), n: ('success', GREEN)}
    if first is not None:
        marks[first] = ('first contact', YELLOW)
    picks = sorted(set(range(0, n + 1, 50)) | set(marks))
    task = {i: im for i, im in enumerate(frames(videos['task_centric'])) if i in picks}
    ego = {i: im for i, im in enumerate(frames(videos['ego'])) if i in picks}
    last = max(task)   # the video has n frames (0 .. n-1); the success boundary n is shown by its last frame
    tiles, small = [], []
    for i in picks:
        j = min(i, last);name, colour = marks.get(i, ('', None))
        text = f't={i * .02:5.2f}s rollout {t0 + i * .02:5.2f}s yaw {s["yaw"][min(i, n)] - yaw0:+5.1f}  {name}'
        tiles.append(label(task[j], text, colour));small.append(label(ego[j].resize((320, 180)), f'{t0 + i * .02:5.2f}s {name}', colour, 3))
    top = grid(tiles, 4);bottom = grid(small, 8)
    sheet = Image.new('RGB', (top.width, top.height + bottom.height + 20), (0, 0, 0))
    sheet.paste(top, (0, 0));sheet.paste(bottom, (0, top.height + 20))
    ImageDraw.Draw(sheet).text((4, top.height + 4), 'ego (half size), same times', fill=(255, 255, 255))
    sheet.save(target / 'sheet.jpg', quality=88)
    # ---- side by side with the production demonstration from the same tick
    demo = state(ideal_dir / f"{segment['case_id'][-3:]}-reset.npz")
    k0 = segment['takeover_tick'] // 10;m = len(demo['t']) - 1 - k0
    demo_video = BASE / f'videos/chunk-000/observation.images.task_centric/episode_{base_index:06d}.mp4'
    demo_frames = frames(demo_video, start=k0)
    corr_frames = frames(videos['task_centric'])
    length = max(n, m);compare, pairs = [], []
    last_c = last_d = None
    def composed():
        nonlocal last_c, last_d
        for i in range(length):
            c = next(corr_frames, None) if i < n else None
            d = next(demo_frames, None) if i < m else None
            last_c = c if c is not None else last_c;last_d = d if d is not None else last_d
            ci, di = min(i, n), min(i, m)
            left = label(last_c, f'corrective E*  rollout {t0 + i * .02:5.2f}s  yaw {s["yaw"][ci] - yaw0:+5.1f}' + ('  SUCCESS' if i >= n else ''), GREEN if i >= n else None, 3)
            right = label(last_d, f'production demo  rollout {t0 + i * .02:5.2f}s  yaw {demo["yaw"][k0 + di] - demo["yaw"][0]:+5.1f}' + ('  SUCCESS' if i >= m else ''), GREEN if i >= m else None, 3)
            im = Image.new('RGB', (1280, 360));im.paste(left, (0, 0));im.paste(right, (640, 0))
            if i % 50 == 0 or i == length - 1:
                pairs.append(im.resize((640, 180)))
            yield im
    encode(target / 'compare.mp4', (1280, 360), 50, composed())
    grid(pairs, 3).save(target / 'compare.jpg', quality=85)
    dfirst = np.flatnonzero(demo['contact'][k0:])
    metrics = {'uid': uid, 'scene': segment['case_id'], 'point': segment['point'], 'takeover_s': t0, 'end_s': t0 + n * .02, 'margin_s': 40. - (t0 + n * .02),
               'duration_s': n * .02, 'first_contact_s': None if first is None else t0 + first * .02,
               'x_hi_cm': float(s['x_hi_cm'][-1]), 'x_lo_cm': float(s['x_lo_cm'][-1]), 'final_yaw_deg': float(s['yaw'][-1] - yaw0),
               'min_yaw_deg': float((s['yaw'] - yaw0).min()), 'out_of_range_share': float(oor.mean()), 'foot_lateral_cm_at_takeover': segment['at_takeover']['foot_lateral_cm'],
               'entry_decision': segment['entry_decision'],
               'demo': {'end_s': float(demo['t'][-1]), 'first_contact_s': float(demo['t'][k0 + dfirst[0]]) if len(dfirst) else None,
                        'final_yaw_deg': float(demo['yaw'][-1] - demo['yaw'][0]), 'min_yaw_deg': float((demo['yaw'] - demo['yaw'][0]).min()),
                        'x_hi_cm': float(demo['x_hi_cm'][-1]), 'x_lo_cm': float(demo['x_lo_cm'][-1]), 'video': str(demo_video), 'renderer': 'EGL (base release)'},
               'files': {p.name: {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(target.iterdir())}}
    (target / 'metrics.json').write_text(json.dumps(metrics, indent=1) + '\n')
    return metrics


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--run', type=Path, required=True);p.add_argument('--out', type=Path, required=True)
    p.add_argument('--ideal', type=Path, required=True);p.add_argument('--scenes', nargs='+', required=True)
    a = p.parse_args()
    run, out = a.run.resolve(), a.out.resolve()
    _, segments = load_segments(run)
    contract = json.loads((BASE / 'meta/contract.json').read_text())
    base_index = {e['episode_uid']: e['episode_index'] for e in contract['episodes']}
    chosen = [s for s in segments if s['case_id'][-3:] in a.scenes]
    results = []
    for s in sorted(chosen, key=lambda s: a.scenes.index(s['case_id'][-3:])):
        if s['case_id'] not in base_index or not s['case_id'].startswith(TASK):
            raise SystemExit(f"{s['case_id']} not in the base release")
        results.append(one(run, out, a.ideal.resolve(), s, base_index[s['case_id']]))
        print(json.dumps({k: results[-1][k] for k in ('uid', 'end_s', 'final_yaw_deg', 'min_yaw_deg')}), flush=True)
    (out / 'metrics.json').write_text(json.dumps(results, indent=1) + '\n')


if __name__ == '__main__':
    main()
