"""Contact sheets of corrective episodes from the released Canonical videos (sft-v1/QLM-DATA-001), both views, one tile every `step` frames.

Usage: corrective_contact_sheet.py RELEASE RUN OUT_DIR UID [UID ...] [--step 16]
Each tile is labelled with the episode time, the absolute rollout time and the routine phase of that frame's command.
"""
import argparse, json
from pathlib import Path
import av
from PIL import Image, ImageDraw

p = argparse.ArgumentParser(); p.add_argument('release', type=Path); p.add_argument('run', type=Path); p.add_argument('out', type=Path)
p.add_argument('uids', nargs='+'); p.add_argument('--step', type=int, default=16); p.add_argument('--cols', type=int, default=6)
a = p.parse_args()
contract = json.loads((a.release / 'canonical/meta/contract.json').read_text())
info = json.loads((a.release / 'canonical/meta/info.json').read_text())
index = {e['episode_uid']: e for e in contract['episodes']}
a.out.mkdir(parents=True, exist_ok=True)
for uid in a.uids:
    ep = index[uid]; n = ep['length']
    prov = json.loads((a.release / 'canonical/metadata' / uid / 'provenance.json').read_text())
    t0 = prov['source_identity']['corrective']['takeover']['absolute_time_s']
    phases = [json.loads(l)['extensions']['expert']['phase'] for l in (a.run / 'traces' / uid / 'commands.jsonl').read_text().splitlines()]
    picks = sorted(set(list(range(0, n, a.step)) + [n - 1]))
    rows = []
    for key in ('observation.images.task_centric', 'observation.images.ego'):
        path = a.release / 'canonical' / info['video_path'].format(episode_chunk=0, episode_index=ep['episode_index'], video_key=key)
        frames = {}
        with av.open(str(path)) as c:
            for i, f in enumerate(c.decode(video=0)):
                if i in picks: frames[i] = f.to_image()
        assert len(frames) == len(picks), (uid, key)
        tiles = []
        for i in picks:
            im = frames[i].copy(); d = ImageDraw.Draw(im)
            d.rectangle([0, 0, 330, 14], fill=(0, 0, 0)); d.text((3, 1), f'frame {i}  t={i*0.02:.2f}s  (rollout {t0+i*0.02:.2f}s)  {phases[i]}', fill=(255, 255, 0))
            tiles.append(im)
        rows.append(tiles)
    w, h = rows[0][0].size; cols = a.cols; per = (len(picks) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * w, 2 * per * h))
    for r, tiles in enumerate(rows):
        for i, im in enumerate(tiles):
            sheet.paste(im, ((i % cols) * w, (r * per + i // cols) * h))
    name = a.out / f'{uid}.jpg'; sheet.save(name, quality=88); print('saved', name, sheet.size, 'frames', n)
