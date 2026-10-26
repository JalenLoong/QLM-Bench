---
id: QLM-SIM-023
type: exec-plan
status: completed
source_map: []
---
# RL-v2 local M1–M4

User explicitly authorized implementation on 2026-10-25.

## Scope
M1 CPU GT replay and full anchor/history restoration; M2 true SFT candidates and calibrated rewards; M3 Dual-NFT and local tiny-model recovery; M4 H>1, distributed and AMD handoff.

## Fixed semantics
Global B2/G4; up to8 dynamic strata; native9/force-zero; NativeCPU/RAMBOCPU/OSMesa; full video endpoint25/50NFE,CFG1,window8. Three rewards .70/.25/.05. First joint chunk only; separate generation/execution/controllability masks. Partial terminal observed/absorbing weighting; full legal first endpoints retained. Empty preference rounds skip optimizer/scheduler but update EMA .9; incomplete infrastructure rounds do not advance. Beta .1; LR1e-6; reference .01.

## Progress
- Worktrees and paired records created. Runtime implementation and gates pending.

## Validation and recovery
Each stage requires actual evidence. Preserve attempts and immutable inputs; resume only committed outer boundaries. QLM execution uncertainty poisons session. Infrastructure at most one same-seed retry. No silent demo replacement or reward-threshold tuning.

## Evidence
workspace runs/audit/rl-v2-local-m1-m4-20261025-v1/

## Not run
AMD/Slurm, full5B backward, formal RL training/evaluation, GitHub/HF/W&B remote writes.

## Completed local acceptance — 2026-10-26

M1: selected push-approved-20261014-01, two successful447-command NativeCPU/RAMBOCPU/OSMesa replays;27 anchors and34 continuation checks, qpos/qvel/RGB exact. Real VAE prefix and decoder branching verified; cache v2 binds actual VAE parameters/config.

M2:32 actual SFT H1 candidates plus4 H2;8 strata and8 meaningful preference groups. Actual repeated replay establishes epsilon_gap; no SFT optimizer updates. Original candidate records and source snapshots remain unchanged.

M3: tiny CPU/CUDA continuous8 versus4+resume4 is exact for all roles,optimizer,scheduler,sampler,statistics andPython/NumPy/Torch/CUDA RNG. Current/EMA export same-prefix/noise endpoints are exact. CUDA flex/reference meets declared BF16 tolerance; gradient cosine0.99999988. Tiny CUDA peak reserved104MiB. Actual offline W&B spools complete, no sync/upload.

M4: actual2/8-rank Gloo gradient equivalence, four empty ranks, collective abort and2-rank checkpoint recovery pass. H3 uses a declared diagnostic feedback policy with actual CPU/RAMBO/VAE, not SFT. No.git relocated resume and actual CPU zero-step restore, README syntax and six-stage preview pass.

Validation: WAM193 unique passed/20 legacy optional skips; QLM555 unique passed/16 optional skips across required environments. The original source-order test was stale on the base branch; corrected to inspect the shared implementation and supplemented by an actual tensor-offset test. The existing PhysX config test passed in the pinned Isaac environment, with no Isaac simulation. Final affected checks25 WAM/12 QLM passed.

Discoveries preserved: missing OSMesa search path before any physics; initial diagnostic global Python/NumPy RNG not seeded consistently (model/optimizer recovery already exact), corrected and completely reverified; VAE cache weight binding strengthened with unchanged cached tensors; old legacy test/environment findings preserved.

Scope completion: M1–M4 local only. Full5B backward, AMD connection/Slurm, formal RL/evaluation and remote writes remain not_run. Source is uncommitted/unpushed. Evidence: workspace runs/audit/rl-v2-local-m1-m4-20261025-v1/completion.json.
