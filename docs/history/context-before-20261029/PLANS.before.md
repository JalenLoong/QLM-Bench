# Work-plan protocol

Use one Work ID for every multi-file change. Before implementation, create a ChangeSpec
under `docs/changes/active/<WORK-ID>/` and an ExecPlan under
`docs/work/active/<WORK-ID>/`. Record assumptions, affected contracts, validation, and
explicitly not-run items. On completion, move both documents to the corresponding
`archive/` tree with `status: completed`; do not leave duplicate active copies.

Semantic changes to action, camera, timing, data labels, model interfaces, or evaluation
also require an ADR and an update to the relevant `docs/current/` page only after the
evidence threshold stated in the ChangeSpec is met.

Run manifests are immutable records of actual attempts. Start from
`docs/templates/run-manifest.yaml`; do not create a manifest for a planned or unrun job.

Governance: read docs/governance/documentation.md and docs/governance/v2.md before multi-file work. Reserve CATEGORY-NNN in docs/governance/work-registry.json; v2 numbering starts at 001 independently of v1, shared across both repositories. Use the same Work ID in changes, plans, commit/PR titles and attempts. See docs/work/INDEX.md.

## OPD-004 current-design amendment —2026-10-24
Use the paired docs/governance/opd-v4-work-registry.json for OPD work. Current accepted
native1/2/400S target is documented by ADR-0002 and the documentation-sync report.
The dated native2/4 branch description is historical implementation scope. Code changes
remain pending authorization; preserve old ADRs,archives,receipts and SFT/QLM identities.

## OPD-005 current implementation
Current code is native1/2,400S/1200F,3F→1S,checkpoint every100 with full S200/S400 protection.
Use the OPD registry and latest current delivery. Old OPD-004 pending-code statements are historical;
AMD/true8streams/formal400S remain separate execution gates. Preserve immutable old ADRs/archives.

## OPD-008 administrator route
Use the independent Stage2-only OPD Slurm chain and current/opd-v4-slurm-008.md report.
Do not route OPD through the retained legacy SFT submitter. Stage1 stays disabled in this chain.
