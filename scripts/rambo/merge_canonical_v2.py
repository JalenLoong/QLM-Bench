"""Compatibility CLI for byte-preserving QLM episode merging."""
import argparse,json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from qlm_bench.compatibility.dataset_v2.merge import merge
from qlm_bench.compatibility.dataset_v2.media import MediaTools

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--entries',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffmpeg',required=True);p.add_argument('--ffprobe',required=True);p.add_argument('--work-id',default='DATA-005');args=p.parse_args()
    print(json.dumps(merge(json.loads(args.entries.read_text()),args.output,MediaTools(args.ffmpeg,args.ffprobe),args.work_id)),flush=True)
