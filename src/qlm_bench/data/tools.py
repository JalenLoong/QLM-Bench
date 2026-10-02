"""Explicit CPU Raw conversion, merge and portable local review entrypoints."""
from __future__ import annotations

import html
import json
import os
from pathlib import Path
from urllib.parse import quote


def convert_raw(raw, canonical, *, ffmpeg, ffprobe):
    """Convert a fresh captured episode, never rewrite an already published one."""
    capture = json.loads((Path(raw) / "capture.json").read_text())
    task = capture["profile"]["task_profile_version"]
    if task.startswith("lift-basket-"):
        from qlm_bench.compatibility.dataset_v2.conversion_lift import convert
    elif task.startswith(("push-box-", "press-button-")):
        from qlm_bench.compatibility.dataset_v2.conversion import convert
    else:
        raise ValueError("Raw conversion requires a supported explicit task profile")
    return convert(raw, canonical, ffmpeg=ffmpeg, ffprobe=ffprobe)


def merge_episodes(entries, destination, *, ffmpeg, ffprobe, work_id):
    from qlm_bench.compatibility.dataset_v2.merge import merge
    from qlm_bench.compatibility.dataset_v2.media import MediaTools
    return merge(entries, destination, MediaTools(ffmpeg, ffprobe), work_id)


def validate_data(config, *, raw=False):
    from qlm_bench.compatibility.dataset_v2.validation import DataPaths, validate_raw, validate_canonical
    paths = DataPaths.from_config(config)
    if raw:
        return validate_raw(paths.dataset_root, tools=paths.tools)
    return validate_canonical(paths.canonical_root, tools=paths.tools)


def build_replay(canonical_root, output):
    """Review exact Canonical videos plus pre-reset terminal frames, without Isaac.

    This HTML references existing local files; it does not re-encode or publish
    them. Timestamp labels use source nanoseconds rather than invented frame time.
    """
    from pyarrow import parquet
    from . import under
    canonical = Path(canonical_root).resolve()
    output = Path(output)
    if output.exists():
        raise ValueError("Refuse existing replay output")
    contract = json.loads((canonical / "meta/contract.json").read_text())
    info = json.loads((canonical / "meta/info.json").read_text())
    rows = []
    def url(relative):
        return quote(os.path.relpath(under(canonical, relative), output.parent.resolve()).replace(os.sep, "/"), safe="/.")
    for episode in contract["episodes"]:
        index = episode["episode_index"]
        path = info["data_path"].format(episode_chunk=index // info["chunks_size"], episode_index=index)
        times = parquet.read_table(under(canonical, path), columns=["simulation_time_ns"])["simulation_time_ns"].to_pylist()
        rows.append({"uid": episode["episode_uid"], "instruction": episode["task_text"], "timestamps_ns": times,
                     "terminal_timestamp_ns": episode["terminal"]["simulation_time_ns"],
                     "videos": {key: url(value["path"]) for key, value in episode["videos"].items()},
                     "terminal": {key: url(value["path"]) for key, value in episode["terminal"]["images"].items()}})
    data = json.dumps(rows, ensure_ascii=False, allow_nan=False).replace("<", "\\u003c")
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>QLM-Bench local Canonical replay</title><style>body{font:16px system-ui;max-width:1400px;margin:2rem auto;padding:0 1rem;background:#f4f6f7;color:#19313e}.views{display:flex;gap:1rem}.view{flex:1;min-width:0}video,img{width:100%}button,select{font:inherit;padding:.5rem}@media(max-width:700px){.views{display:block}}</style>
<h1>QLM-Bench local Canonical replay</h1><p>Existing source videos and pre-reset terminal frames. This review is not a learned-policy benchmark result.</p>
<select id="episode"></select><button id="play">Play both</button><button id="pause">Pause</button><p id="description"></p><p id="clock"></p>
<div class="views"><div class="view"><h2>Ego</h2><video controls></video><img alt="Ego terminal snapshot"></div><div class="view"><h2>Task</h2><video controls></video><img alt="Task terminal snapshot"></div></div>
<script>const rows=__ROWS__,select=document.querySelector('select'),videos=[...document.querySelectorAll('video')],images=[...document.querySelectorAll('img')];
const keys=['observation.images.ego','observation.images.task_centric'];let current;
for(const row of rows){const option=document.createElement('option');option.value=row.uid;option.textContent=row.uid;select.append(option)}
function show(){current=rows.find(r=>r.uid===select.value);document.querySelector('#description').textContent=current.instruction;videos.forEach((v,i)=>{v.src=current.videos[keys[i]];images[i].src=current.terminal[keys[i]]});document.querySelector('#clock').textContent='Terminal source time: '+current.terminal_timestamp_ns+' ns';}
select.onchange=show;document.querySelector('#play').onclick=()=>videos.forEach(v=>{v.currentTime=0;v.play()});document.querySelector('#pause').onclick=()=>videos.forEach(v=>v.pause());
videos[0].ontimeupdate=()=>{const frame=Math.min(Math.floor(videos[0].currentTime*50),current.timestamps_ns.length-1);document.querySelector('#clock').textContent='Source simulation_time_ns: '+current.timestamps_ns[frame]+' · terminal '+current.terminal_timestamp_ns+' ns'};show();</script></html>'''
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page.replace("__ROWS__", data))
    return {"passed": True, "episodes": len(rows), "output": str(output.resolve()), "media_reencoded": False}

