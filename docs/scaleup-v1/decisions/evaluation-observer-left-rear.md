---
id: QLM-EVALUATION-OBSERVER-LEFT-REAR
type: decision
status: accepted
related_work: [QLM-EVAL-002]
source_map: [src/qlm_bench/backends/mujoco/render.py, src/qlm_bench/backends/mujoco/suite.py, src/qlm_bench/backends/mujoco/evaluation.py]
---

# Uniform evaluation observer

The user2026-10-18 requests a consistent left-rear, slightly elevated observer for all evaluation tasks, farther from the robot to include the whole body. Evaluation enables a render-only observer override: eye[-0.70,1.55,0.85]m and target[0.10,0,-0.10]m relative to base translation/heading; vertical FoV35deg and stable world-up. Both Standard/learned and original engineering adapters enable the same override. Production rendering and both policy cameras retain their original geometry. No MjModel or physics parameters change.

One retained Press engineering episode was re-rendered from its measured0–4s states, with no new policy or physics. The51-frame preview and three inspected frames show the complete robot. Actual GL was EGL/Mesa llvmpipe; this is a camera framing check, not new hardware-reference or benchmark admission. Other tasks were not rendered. Existing36 evaluation contract checks pass.

The same user explicitly authorizes evicting evaluation development episodes, media/state/action payloads, staging/readback copies and caches. Compact historical outcomes, failures, source identities and publication receipts remain; old run paths are historical after eviction. Original training data, assets, weights, encoders, prompts and normalizers remain. Evidence: workspace runs/audit/mujoco-eval-observer-cleanup-20261018-v1/. The implementation/render/cleanup stage made no remote mutation or source commit/push. At the initial camera-only stage, published source snapshots remained unchanged; QLM-EVAL-003 subsequently performed the explicitly authorized new source freeze/publication.

The user subsequently accepted this view and authorized committing QLM-EVAL-002 locally, explicitly excluding GitHub push. The [cleanup receipt](../evidence/QLM-EVAL-002/cleanup-receipt.json), [render receipt](../evidence/QLM-EVAL-002/render-receipt.json), [exact compressed deletion inventory](../evidence/QLM-EVAL-002/deletion-inventory.jsonl.gz) and [evidence index](../evidence/QLM-EVAL-002/evidence-index.json) preserve the executed checks and user acceptance in Git. Media/cache payloads remain excluded.

QLM-EVAL-003 now publishes source `8456b9ab352445028340315627ed0a40087cf421` in private dataset revision `575d4a3726896d498ed4fb76710948b2fbea7cdd` with refreshed archive, source manifest, protocol/registry identities and complete hash bindings. Historical reset/engineering evidence keeps its original source identity. The [source publication receipt](../evidence/QLM-EVAL-003/final-hf-verification.json) confirms the update without any additional episode run.
