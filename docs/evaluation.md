---
id: QLM-EVALUATION
type: guide
status: accepted
source_map: []
---
# Evaluation infrastructure and result completeness

EvalCase records task/assets/initial physical state/goal/cameras/seeds/runtime/controller,
reset procedure and actual reconstruction evidence. Unverified cases stay draft.
Protocols declare horizon, expected trial set and metric/error policy. No formal default
suite is created. Policy providers receive only allowed observation/context; experts may
use explicitly marked privileged state, not a learned-policy observation leak.

Every expected trial is represented, including errors/not_run/retries. Metrics and result
publication require the declared completeness rules. Fixture/source-only checks are local
engineering evidence and cannot become a formal benchmark score. Terminal RGB/state is
owned before reset. The current adapter does not implement WAM transport or networking.
