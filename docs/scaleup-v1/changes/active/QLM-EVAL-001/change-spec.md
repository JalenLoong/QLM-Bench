---
id: QLM-EVAL-001
type: change
status: active
source_map: []
---

# Ten-task MuJoCo evaluation and private resource delivery

Implement ten-task learned evaluation via existing synchronous driver, freeze test100, preserve training bytes, run22 bounded old-Isaac-policy engineering episodes, publish private HF resources/suite; local commits only.

Explicit user authorization:2026-10-18. Evidence:workspace runs/audit/mujoco-evaluation-20261018-v1/. Keep AMD checkout and historical attempts immutable.

## Acceptance

100 actual zero-step case reconstructions;22 real bounded episodes; complete CPU/contract and separate v2/v3 training consumer checks; exact HF protected-tree and resource readback. Formal benchmark/SR/AMD/training are not run. Failed and partial attempts remain explicit.

## Progress

- [x] Read sources and establish protected baseline.
- [ ] Implementation and CPU checks.
- [ ] Local source freeze and actual runtime/consumer checks.
- [ ] Private HF resource/suite publication and readback.
- [ ] Evidence reconciliation and paired archive.
