---
id: QLM-RL-V2-ENVIRONMENT
type: research
status: completed
source_map:
  - src/qlm_bench/backends/mujoco/rl_v2/snapshot.py
  - src/qlm_bench/rl_v2/worker.py
  - src/qlm_bench/rl_v2/evaluation.py
---

This is the historical ALG-001/QLM-SIM-023 implementation record. The user-approved 2026-10-26 LoRA/ten-demo profile supersedes its training settings; see the current RL page and WAM README. Original evidence remains unchanged.
# RL-v2 CPU environment

QLM-SIM-023 pairs with WAM mujoco-v2/ALG-001. Physics, RAMBO, renderer and task
predicates remain QLM-owned; no WAM/model/reward dependency enters the worker.

Explicit preparation entrypoints are qlm_bench.backends.mujoco.rl_v2.replay and
qlm_bench.rl_v2.verification. Replay validates the selected train lineage and actual
software renderer. Snapshots contain full MuJoCo integration, controller/motor/gait,
task, clocks, RNG and command state. Restore retains absolute time and advances its
identity epoch. Only verified complete-group boundaries are admitted.

qlm_bench.rl_v2.worker provides bounded lossless framed JSON IPC, exactly-once request
identities, explicit restore, execute and inspect. Uncertain failures poison the
session; expired responses cannot execute again. Terminal scoring returns actual
partial RGB without padding model history. Finite unrepresentable commands are
labelled policy rejection without inventing task failure or advancing physics.

qlm_bench.rl_v2.evaluation derives a separately named OSMesa profile from the frozen
Standard suite, with actual zero-step case reconstruction. Its run entry uses normal
task initial states and the existing task evaluator/SynchronousDriver. Original EGL
checks remain intact. CPU target deployment must regenerate/verify reference artifacts
when its controller/runtime/renderer identity differs.

Local real replay, all27 anchors and2-chunk SFT feedback have evidence under workspace
runs/audit/rl-v2-local-m1-m4-20261025-v1/. Full regression and paired archive closeout are complete in the
archived plan. AMD and formal RL evaluation are not_run. Original runs/data are unchanged.

## Completed local acceptance — 2026-10-26

M1: selected push-approved-20261014-01, two successful447-command NativeCPU/RAMBOCPU/OSMesa replays;27 anchors and34 continuation checks, qpos/qvel/RGB exact. Real VAE prefix and decoder branching verified; cache v2 binds actual VAE parameters/config.

M2:32 actual SFT H1 candidates plus4 H2;8 strata and8 meaningful preference groups. Actual repeated replay establishes epsilon_gap; no SFT optimizer updates. Original candidate records and source snapshots remain unchanged.

M3: tiny CPU/CUDA continuous8 versus4+resume4 is exact for all roles,optimizer,scheduler,sampler,statistics andPython/NumPy/Torch/CUDA RNG. Current/EMA export same-prefix/noise endpoints are exact. CUDA flex/reference meets declared BF16 tolerance; gradient cosine0.99999988. Tiny CUDA peak reserved104MiB. Actual offline W&B spools complete, no sync/upload.

M4: actual2/8-rank Gloo gradient equivalence, four empty ranks, collective abort and2-rank checkpoint recovery pass. H3 uses a declared diagnostic feedback policy with actual CPU/RAMBO/VAE, not SFT. No.git relocated resume and actual CPU zero-step restore, README syntax and six-stage preview pass.

Validation: WAM193 unique passed/20 legacy optional skips; QLM555 unique passed/16 optional skips across required environments. The original source-order test was stale on the base branch; corrected to inspect the shared implementation and supplemented by an actual tensor-offset test. The existing PhysX config test passed in the pinned Isaac environment, with no Isaac simulation. Final affected checks25 WAM/12 QLM passed.

Discoveries preserved: missing OSMesa search path before any physics; initial diagnostic global Python/NumPy RNG not seeded consistently (model/optimizer recovery already exact), corrected and completely reverified; VAE cache weight binding strengthened with unchanged cached tensors; old legacy test/environment findings preserved.

Scope completion: M1–M4 local only. Full5B backward, AMD connection/Slurm, formal RL/evaluation and remote writes remain not_run. Source is uncommitted/unpushed. Evidence: workspace runs/audit/rl-v2-local-m1-m4-20261025-v1/completion.json.
