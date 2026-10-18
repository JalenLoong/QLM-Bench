---
id: QLM-MUJOCO-STANDARD-EVALUATION
type: current
status: accepted
source_map: []
---

# MuJoCo ten-task evaluation and resource delivery

QLM-EVAL-001 implements the user-approved2026-10-18 local evaluation/resource scope. The frozen candidate suite is mujoco-standard-test100-v1: ten held-out test configurations per task,2Clean8Randomized, original environment seeds and policy seed42. Task horizons: Push/Press/Lift/Kick24s;Sweep/Fridge/Drawer40s;Valve32s;Oven/Room Door60s. NativeCPU/originalRAMBOCPU/EGL is the explicit reference route. Formal policy trials and SR are not run by this work.

`python -m qlm_bench.cli evaluate prepare-standard` requires explicit published snapshot, authorization, new staging output and source commit. `verify-standard` requires resource-root/suite and writes actual zero-step reconstruction/RGB evidence. `run-learned` requires explicit resource-root/suite/policy-port/policy-identity/output. `--engineering --case-id ID` selects the first Clean member per declared task for bounded4s checks; `--repeat-push` verifies the same runtime/service across two Push resets. No expert/stand substitution occurs in this path. Existing engineering prepare/run remain available.

The public EvaluationRunner owns trial completeness/results and supports the original single-command path plus SynchronousDriver chunk16 execution. Infrastructure errors remain in an immutable attempt chain; explicit previous-result recovery retries only error/not_run slots with identical case/policy seed. A valid failure/timeout is never selected away. Incomplete Standard slots cannot produce SR.

Scene packs retain their original bytes and portable manifests under assets/ASSET/RESOURCE_IDENTITY/runtime. A qlm-resource-manifest-v1 outer manifest binds files, origin, license evidence and entrypoint. The original three-file RAMBO closure is mirrored under assets/rambo-go2-controller/iteration-2000/runtime; its independent HF model remains unchanged. The user's private-dataset redistribution confirmation is scoped evidence, not a new blanket SPDX grant.

benchmarks/mujoco-standard-test100-v1 contains cases, protocol/resource registry snapshots, actual reconstruction evidence and explicit source archives. Source archives are binary artifacts with their own hashes, not JSON snapshots. Training catalog/DataRefs/splits/prompt and payload remain unchanged. Policy weights/normalizers/prompt embeddings/frozen encoders stay WAM-owned. A single live episode requires only its declared resource closure, not all1000 demonstrations.

User-authorized local engineering uses original Isaac50 v2/v3 step1000 SFT weights at HF223634bc64bc225881de80c2ac6e38c1de713a93 with their own original normalizers; the current exact MuJoCo task embeddings are separately identified. These are engineering observations, not MuJoCo SFT performance. Source commits stay local; no GitHub push or AMD access. Current evidence and all failed attempts are in workspace runs/audit/mujoco-evaluation-20261018-v1/.

## Verified delivery2026-10-18

100 Standard cases and22 real old-Isaac policy engineering episodes verified; private HF training+evaluation main=254d4f0673e2698bcb74375f130aa88a344aa762; training bytes/DataRefs/splits/prompts preserved; local commits only. Formal benchmark/SR,training,AMD and GitHub push not run. Evidence:workspace runs/audit/mujoco-evaluation-20261018-v1/.
