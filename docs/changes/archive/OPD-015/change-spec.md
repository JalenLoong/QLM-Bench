---
id: OPD-015
type: change
status: completed
source_map: []
---
# Quadrupedal OPD review follow-up: reviewed runtime equivalence, AMD blockers and prediction video

User asked to review OPD-014 against the administrator's actual runs, remove remaining
identity/over-defensive checks that stop AMD runs, and add training-time video prediction
visualization as a periodic closed-loop rollout. Algorithm, recipe, data split and success
criteria are unchanged; OPD-014 is reviewed, not reimplemented.

- [x] Review OPD-014 against the administrator's W&B eight-smoke config: QLM legacy source
      `c00b6cac…`, train pool `dff72924…` and profile `09b9f202…` match the registered legacy path.
- [x] Add reviewed runtime equivalence (`runtime_sha256` + `equivalent_runtime_sha256`): a
      logging-only change to a runtime file no longer invalidates existing smoke reports or
      checkpoints; unknown fingerprints are still rejected.
- [x] Fixed CPU worker settings in `cpu_worker_environment` are overridden with a warning instead
      of rejecting the run (cause of discarded run 79811); PYTHONPATH override is still rejected.
- [x] W&B: failed/interrupted attempts finish with exit code 1 and an error summary; smoke
      summaries carry passed/recovery/HBM/barrier values.
- [x] Large-file content hashes are reused while inode/size/mtime/ctime are unchanged
      (`WAM_FILE_HASH_CACHE` per run root), so stages stop rehashing the SFT weights.
- [x] Formal runs: rank 0 rolls out the current student on one held-out lift_basket validation
      reset every fifth of the run (plus step 0) and logs a composite MP4 (predicted ego/task,
      simulator ego/task, simulator observer). Failures are logged and never stop training.

Paired QLM: new `training_visualization` runner and case file outside the runtime file list;
QLM runtime fingerprint unchanged. Local CPU tests only; no commit/push, AMD, Slurm or full 5B load.
