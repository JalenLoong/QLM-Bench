# RL-v4 open_room_door: task and scene inputs

Branch `rl/v4_window-level_DiffusionNFT_Open_door`, branched from `rl/v4_window-level_DiffusionNFT_Push_box` `1ec7d8a`. The
training, reward and run code is in WAM-Policy on the branch of the same name (`scripts/rl_v4/open_door_nft/`). Push's
inputs (`scripts/rl_v4/push_box/`) are unchanged.

## Scene worker changes (`src/qlm_bench/rl_v3/`, outside `execution_source_identity`)

| file | change |
|---|---|
| `door.py` (new) | door own state: `capture` leaves the `criteria` objects (each holds the 110.8 MB MjModel, which made door states unreadable by the `weights_only` load) out of the task part; `restore` rebuilds every criterion's sticky unlock flag from the restored `unlocked` mirror (the worker reuses one runtime per scene and restore does not call `task.reset()`). Five door columns, pure reads, `observe()` never called: `lever_rad`, `bolt_retraction_m`, `socket_exit_clearance_m`, `unlocked` (the sticky flag), `fl_handle_contact` (FL foot geom touching the `<door>_handle` geom). Records only, no reward uses them |
| `privileged.py` | appends `door.COLUMNS` / `door.values` for open_room_door only |
| `scene_worker.py`, `own_state.py` | capture (ring and `capture_state`) through `door.capture`, restore through `door.restore` |

For every other task `door.capture` / `door.restore` are `snapshot.capture` / `snapshot.restore` themselves and the
columns are unchanged, so push states and rows are as before. `backends/mujoco/rl_v2/snapshot.py` is not touched.

## Files here

| file | content |
|---|---|
| `cases/`, `cases-index.json` | the 80 train EvalCases (16 clean, 64 randomized; case seed 42, horizon 60 s) and their index (case sha256, scene `model_path`, controller sha256); the WAM door run reads them from this directory (`RLV4_DOOR_CASES` overrides) |
| `door_cases.py` | builds those cases: the sweep recipe (`scripts/sft_v1/sweep_cases.py`) with the task changed; 10/10 test scenes rebuilt equal the frozen Standard100 cases |
| `workspace-files.tar.gz` (+ `.sha256`) | the 80 train scene packs without their meshes (xml, json), `v2-inference.json` and `frozen-resources.json`, workspace-relative paths (562 files, 1.1 MB); deterministic, rebuilt by `make_workspace_archive.sh` from `bundle-small-files.txt`; the WAM `prepare` step unpacks it into the workspace |
| `scene-files.json` | sha256 of every file the run reads outside the checkouts and models: the archive's files plus the 2,800 mesh references (24 distinct meshes, the same set as the 10 Standard100 door test scenes), fetched from HF dataset `dontKnow23456/QLM-Bench@f26e8d2b` by sha256 |
| `make_lists.py` | writes `bundle-small-files.txt` and `scene-files.json` |
| `scene-check-picks.json`, `commands/` | three door episode starts (4 chunks before the first handle contact) of the round-0 teacher pool and the executed chunks of their stored episodes from reset, for the scene-worker timing sweep (`tools/scene_check.py sweep` in WAM) |

```bash
PYTHONPATH=src envs/qlm-mujoco-py312-v1/bin/python scripts/rl_v4/open_room_door/door_cases.py --out scripts/rl_v4/open_room_door/cases
python3 scripts/rl_v4/open_room_door/make_lists.py <workspace root>
RLV4_WS=<workspace root> scripts/rl_v4/open_room_door/make_workspace_archive.sh
```
