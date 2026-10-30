---
id: OPD-016
type: exec-plan
status: completed
source_map: []
---
# Quadrupedal OPD: accept unregistered legacy WAM whole-tree source hashes

User decision (2026-10-29): relax only the rejection of an OPD-013 record whose whole-tree WAM
source hash is not registered. That hash covers every `.py` under `wam_policy/` and `wan_va/`, so any
administrator-side edit changes it; it is provenance. Algorithm, recipe, data and success criteria
are unchanged.

- [x] `compatibility.unregistered_legacy_wam`: a 64-hex unregistered WAM hash in a legacy record
      (no `runtime_compatibility`) whose paired QLM hash is registered is accepted as the single
      registered WAM entry of that release; QLM stays registered-only.
- [x] Accepted hashes are printed as a WARNING and recorded as `legacy_source_override`: the run.json
      case in the new execution snapshot; run.json and each admission smoke receipt in the formal
      config (`config.json`, `resolved.json`, W&B config).
- [x] The upgraded checkout's semantic runtime fingerprints, resources, algorithm, profile, pool,
      payload hashes, smoke measurements and env setup stay strict.
- [x] README, ADR-0005 amendment, OPD-014 behaviour page and current handoff updated.

Local CPU tests only; no commit/push, AMD, Slurm or training.

Verification: WAM `make check` 284 passed / 21 skipped. New tests cover:
- an admin-edited run.json plus smoke receipts continuing to formal, with the hashes recorded;
- a receipt-only unregistered hash, also recorded;
- an unknown QLM hash or a malformed WAM hash, still rejected;
- the paired-release rule.
The new tests fail with the relaxation removed. An independent adversarial review found that a receipt-only hash was not recorded; this is fixed. Not run on AMD.

