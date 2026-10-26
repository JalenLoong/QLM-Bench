---
id: QLM-RL-V2-LOCAL
type: current-design
status: accepted
source_map: []
---

Current GitHub source delivery is recorded in [publication status](rl-v2-source-publication.md). Earlier local-only statements below retain their original execution scope.

## Two independent tasks — 2026-10-26

[The dual-task delivery](rl-v2-dual-task.md) adds Sweep Block with the same SFT parent and numerical recipe. Task state/output/HF paths are independent; the user requires only one shared engineering smoke pair. Earlier single-task records retain their historical scope.

## Independent review — 2026-10-26

Current deployment and review repairs are recorded in [the independent review](rl-v2-independent-review.md).
The ten-demo LoRA profile below remains fixed; historical evidence is not retroactively re-certified.

## Current configuration — 2026-10-26

User-approved ten-demo LoRA32/alpha32/dropout0 supersedes the earlier single-demo full-parameter profile below. Two different demos per round, four candidates each, eight strata per demo;120 rounds/960 training candidates. AdamW LR3e-5, warmup10 actual optimizer updates, weight decay0, reference weight.05. Flat rounds skip optimizer/scheduler/EMA; completed outer clock advances. Checkpoint20, current/EMA validation40 on ten held-out Push normal initial states. New references/calibration and formal target execution remain not_run. WAM administrator README is the executable runbook.

The remaining text records prior ALG-001/QLM-SIM-023 evidence and is not acceptance of this new profile.

# RL-v2 local engineering acceptance

Accepted scope is local M1–M4 only; no algorithm-effectiveness or AMD result is claimed.

## Completed local acceptance — 2026-10-26

M1: selected push-approved-20261014-01, two successful447-command NativeCPU/RAMBOCPU/OSMesa replays;27 anchors and34 continuation checks, qpos/qvel/RGB exact. Real VAE prefix and decoder branching verified; cache v2 binds actual VAE parameters/config.

M2:32 actual SFT H1 candidates plus4 H2;8 strata and8 meaningful preference groups. Actual repeated replay establishes epsilon_gap; no SFT optimizer updates. Original candidate records and source snapshots remain unchanged.

M3: tiny CPU/CUDA continuous8 versus4+resume4 is exact for all roles,optimizer,scheduler,sampler,statistics andPython/NumPy/Torch/CUDA RNG. Current/EMA export same-prefix/noise endpoints are exact. CUDA flex/reference meets declared BF16 tolerance; gradient cosine0.99999988. Tiny CUDA peak reserved104MiB. Actual offline W&B spools complete, no sync/upload.

M4: actual2/8-rank Gloo gradient equivalence, four empty ranks, collective abort and2-rank checkpoint recovery pass. H3 uses a declared diagnostic feedback policy with actual CPU/RAMBO/VAE, not SFT. No.git relocated resume and actual CPU zero-step restore, README syntax and six-stage preview pass.

Validation: WAM193 unique passed/20 legacy optional skips; QLM555 unique passed/16 optional skips across required environments. The original source-order test was stale on the base branch; corrected to inspect the shared implementation and supplemented by an actual tensor-offset test. The existing PhysX config test passed in the pinned Isaac environment, with no Isaac simulation. Final affected checks25 WAM/12 QLM passed.

Discoveries preserved: missing OSMesa search path before any physics; initial diagnostic global Python/NumPy RNG not seeded consistently (model/optimizer recovery already exact), corrected and completely reverified; VAE cache weight binding strengthened with unchanged cached tensors; old legacy test/environment findings preserved.

Scope completion: M1–M4 local only. Full5B backward, AMD connection/Slurm, formal RL/evaluation and remote writes remain not_run. Source is uncommitted/unpushed. Evidence: workspace runs/audit/rl-v2-local-m1-m4-20261025-v1/completion.json.
