---
id: OPD-003
type: exec-plan
status: completed
source_map: []
---
# OPD-v4 portability review

Audit paths versus immutable content identity, cross-host configuration, CPU runtime
libraries, model environment and same-host launcher constraints. Fix confirmed defects
and validate with isolated CPU relocation fixtures without Git metadata. Preserve all
prior evidence and resource bytes. No AMD access, full5B loading, GPU tests, dependency
installation or publication. Runtime hardware acceptance remains separate.

- [x] Inspect resource/config/checkpoint bindings and target assumptions.
- [x] Implement location-independent identity, explicit relocation and preflight.
- [x] Verify moved source/resources without .git and negative identity cases.
- [x] Run affected checks and deliver administrator migration notes.

Evidence: workspace runs/audit/opd-v4-portability-review-20261022-v1/.

## Findings and closure
Prompt identity included local paths; frozen-resource identity included packaging JSON
bytes; resume also bound timeout/checkpoint cadence. Separate addresses/operational
settings from semantic/content identity. Keep approved SFT,normalizer,source code,
train-pool and consumed encoder hashes strict. Config-relative paths and explicit
relocate are supported; preserve interpreter symlinks and report unmapped locations.
Cached prompts no longer require unused T5/tokenizer payloads; consumed bytes are also
checked against SFT provenance. Add target interpreter/ROCm/RCCL,CPU OSMesa,ports and
W&B credential-presence preflight before full-model launcher startup. Source tree must
contain its entrypoint/catalogue; CPU source environment cannot be overridden.
QLM prepare uses explicit resource-map when historical scene locations are unavailable;
copy fallback handles filesystems without hardlinks. Preserve hardlinks during transfer:
current pool has about126.2GiB logical files but1.26GiB unique copied content.

CPU tests and relocated/no-Git source + authenticated800pool + tiny checkpoint resume
passed. New inode/mtime did not change learner restore or next-round parameters.
No full5B, GPU compute, AMD connection, physics rollout, dependencies or publication.
See workspace runs/audit/opd-v4-portability-review-20261022-v1/ and current portability note.
