"""User-authorized ten-pilot coordinator. Does not expand to100 or other tasks."""
import argparse,json
from qlm_bench.backends.mujoco.synthesis_queue import run_production
p=argparse.ArgumentParser();p.add_argument('--profile',required=True);p.add_argument('--output',required=True)
p.add_argument('--checkpoint',required=True);p.add_argument('--stop-after-physics',action='store_true');p.add_argument('--limit',type=int)
a=p.parse_args();print(run_production(a.profile,a.output,a.checkpoint,stop_after_physics=a.stop_after_physics,limit=a.limit),flush=True)
