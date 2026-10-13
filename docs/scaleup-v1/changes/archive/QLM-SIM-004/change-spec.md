---
id: QLM-SIM-004
type: change
status: completed
source_map:
  - scripts/rambo/compare_controller_isaac.py
---

# Independent Isaac reference and MuJoCo tracking comparison

## Authority and question
The user requests a standalone original Isaac RAMBO verification against the existing
18s Native/CUDA results, to distinguish pre-existing command/response error from
migration effects and reconsider whether a MuJoCo RAMBO checkpoint needs training.
No retraining or original-task asset migration is authorized by this comparison.

## Matched conditions
Use original Isaac/CRL2 numerical source at189545f, not the new shared RAMBOCore.
Verify original model_2000 weights and normalizers, deterministic seed42, disabled
events/noise/command sampling, nominal root/joint reset and500/100/50Hz schedule.
Replay the QLM-SIM-00318s command schedule. Gait modes/frequencies and motor/QP
configuration retain the original meanings; final gait segment is extended only
to prevent the source ten-second schedule from ending before the diagnostic.
Collect root-link/body velocities, unwrapped yaw, actual FL position, actor/motor
outputs, source/robot/physics/delay identities and actual observer RGB. Termination
must stop before an automatic reset can conceal a failed trajectory.

## Evidence thresholds and attribution
Compare phase means using identical one-second transient exclusion, full time series,
and root pose displacement/yaw integration. Check actor/normalizer identity and command
consumption first. Same schedule alone does not isolate solver causality: identify
robot inertia/collision/friction, motor delays and adapter differences as confounds.
If a large new loss remains, investigate the controlling equations and perform only
bounded, explicitly recorded follow-up checks needed to disambiguate it.
Do not recommend retraining merely because a short target-tracking number is imperfect;
report whether the deficit already exists in Isaac and whether migration adds it.

## Scope exclusions
No model/controller training, optimizer, task asset conversion, changes to frozen
action/observation/camera/data contracts, AMD access, formal demonstrations/evaluation,
commit/push or external upload. Preserve every attempt and prior evidence.
