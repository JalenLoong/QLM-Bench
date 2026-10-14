"""Separate OSMesa worker: no RAMBO/controller/physics execution imports."""
import argparse
import json
from qlm_bench.backends.mujoco.replay_recording import record_trace

p=argparse.ArgumentParser();p.add_argument('--trace',required=True);p.add_argument('--model',required=True)
p.add_argument('--output',required=True);p.add_argument('--episode-uid',required=True)
p.add_argument('--ffmpeg',required=True);p.add_argument('--ffprobe',required=True)
p.add_argument('--metadata');p.add_argument('--batch-source');p.add_argument('--formal-pilot',action='store_true')
a=p.parse_args()
def load(path):
 if not path:return None
 with open(path) as f:return json.load(f)
r=record_trace(a.trace,a.model,a.output,episode_uid=a.episode_uid,ffmpeg=a.ffmpeg,ffprobe=a.ffprobe,
 formal=a.formal_pilot,metadata=load(a.metadata),batch_source=load(a.batch_source))
print({k:r[k] for k in ['passed','n_actions','wall_s','controller_loaded']},flush=True)
