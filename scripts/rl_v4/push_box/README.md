# RL-v4 push_box: task and scene inputs

Branch `rl/v4_window-level_DiffusionNFT_Push_box` (from `sft/v1_task-specific_corrective-SFT` `260bcc4`; `src/` unchanged).
The training, reward and Slurm code is in WAM-Policy on the branch of the same name (`scripts/rl_v4/push_nft/`); its
`prepare` step reads the files below from this checkout. The scene worker the run uses is the unchanged
`qlm_bench.rl_v3.scene_worker`.

| file | content |
|---|---|
| `workspace-files.tar.gz` (+ `.sha256`) | the 80 push_box train scene packs without their large meshes (scene.xml, json, small obj/npz; 8,080 files), the 80 case files and `cases-index.json` of `tsft-push-gate-20261111-v1`, `v2-inference.json` and `frozen-resources.json` (8,163 files, 54 MB raw, 2.0 MB packed), with workspace-relative paths; deterministic, rebuilt by `make_workspace_archive.sh` from the list `bundle-small-files.txt` |
| `scene-files.json` | sha256 of every file the run reads outside the checkouts and models: the archive's files plus the 3,680 large mesh references, which are fetched from HF dataset `dontKnow23456/QLM-Bench@f26e8d2b` by sha256 |
| `scene-check-picks.json`, `commands/` | three push states after first contact and the executed chunks of their stored episodes from reset, for the scene-worker snapshot/restore check (`tools/scene_check.py` in WAM) |
