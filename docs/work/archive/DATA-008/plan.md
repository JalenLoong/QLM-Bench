---
id: DATA-008
type: exec-plan
status: completed
source_map: []
---
# Press the button: external asset review and one technical pilot

## Authorized scope and approval boundary
User approved a new external button asset, vertical mounting and forward FL pressing. Keep Go2, FL, native9, original controller/checkpoint, force-zero, native robot reset origin and existing ego/task camera geometry. Raw/Canonical50Hz, observer25Hz monitor-only; authoritative simulation timestamps and terminal-before-reset remain strict. Text: Press the button.

First priority: Industrial Button by mark_saba (Sketchfab a7e7c1772d764c3b913cccac66932236), backup Emergency Stop Button by phoenix-storms (012e4809a41445ca9de17286f677fabb). Both official APIs report downloadable and CC BY4.0. Downloads require authenticated access. User opted to log in and retain the first candidate. No preview extraction or old self-built button fallback.

Asset structure/texture/dimensions/movable cap, collision/slide/spring additions and provenance must be inspected. Produce three-view approach/pre-contact/pressed-state review plus concrete dimensions, placement, stroke, success threshold and spring parameters. Static review poses must be explicitly distinguished from physical demonstrations. User must approve this concrete asset/geometry package before freezing it or starting the pilot.

## Implementation after asset review
Independent task profile and scripted high-level expert; no learned controller changes or object animation/teleport/external wrench as success. Success requires actual axial button displacement at reviewed threshold, not fallen, for3 consecutive50Hz policy ticks; release/rebound not required. Contact stays unknown diagnostic and never gates success. Success-driven debug indicators excluded from policy RGB.

Replace box-specific recorder/packager assumptions through task mapping without changing core schemas or old Push Box behavior. task.goal.position is the task-defined press target; task.progress is measured axial displacement. Cap pose/axis/stroke/threshold/hold counts live in named extensions. Preserve robot state and confirmed actions for future v3 consumers.

## Checks and attempt limits
CPU threshold/hold/fall/reset/task-mapping tests and Push Box regression checks. Real reset isolation and pre-reset terminal capture before pilot. Pilot max20sim seconds/1000 completed50Hz actions, at most3 capture attempts; stop on program errors before any retry, preserve every failed attempt. No silent extra budget or relaxed criterion. Validate RawN/N+1, CanonicalN plus terminal, media/timestamps/action continuity and three-view behavior. No WAM cache/training, batch collection, HF upload, commit or push.

## Repository isolation
RAMBO v2 owns implementation. WAM authority registry is updated only in separate detached worktree repos/WAM-Policy-v2-press-button from current local v2 ref; active WAM v3 and existing v2-hash-policy worktree remain unchanged. RAMBO registry receives existing WAM-only TRAIN-002/003/004/005 entries as authoritative synchronization, not new training authorization. This task does not authorize any training.

## Progress
- [x] Confirm scope, source availability/license and current repository separation.
- [x] Obtain authenticated source archive and inspect actual structure/geometry.
- [x] Produce asset/scene/camera review package and obtain user approval.
- [x] Implement task adapter and collector; run CPU/reset checks.
- [x] Acquire and validate one technical pilot, then stop for user review.

## Evidence
runs/audit/v2/DATA-008/20260926T055824Z

## Asset review ready, awaiting user decision

Industrial Button original FBX archive and official USDZ downloaded from authenticated official UI. Source hashes and current/embedded author discrepancy preserved. Independent cap mesh found. Review-only meter/Z-up derivative uses source materials; no old procedural button appearance. Three static review runs completed, zero pilot attempts. Current proposal: cap front(.56,.10,.30)m, cap diameter8.85cm, overall17.9cm width/height, stroke20mm, threshold12mm/3 policy ticks, cap mass.10kg, spring300N/m, damping8N.s/m, max effort40N. Propose front observer(-.25,1.3,.95)m looking at(.45,.1,.22)m; dual policy cameras unchanged. Near ego is partly occluded by FL, task view shows cap/foot. All proposals pending user approval; no physical press success, terminal-before-reset or data acceptance claimed. Review evidence: workspace runs/audit/v2/DATA-008/20260926T055824Z; page review.html.

The RAMBO docs checker reports two pre-existing overview links to WAM v2 files missing from active WAM v3. They were not modified in this task. Isolated v2 docs and shared governance pass; import boundaries pass. No code/data changes in active WAM v3.

## User approval and implementation

User approved the review and explicitly prohibited all WAM v3 changes. Approval receipt: user-asset-approval.json in DATA008 evidence. Frozen profile press-button-v2-1 and native9 scripted expert implemented in RAMBO. CPU tests243 passed/1 skipped/1CUDA deselected. Terminal-gate-01 passed32 actions/33 boundaries, actual pre-reset copies and reset isolation. pilot-a1 is the first of at most3 capture attempts; outcome must be read from actual report. See [task semantics](../../../decisions/ADR-0011.md).

## Technical pilot completed

After explicit asset approval, pilot-a1 completed20s with valid terminal/data recording but failed to press the button due to lateral base drift and EEF misalignment; preserved and excluded. Upper-level base-Y/yaw feedback, EEF alignment and bounded X hold corrected the behavior without changing reviewed assets, physical parameters, threshold or controller. Fresh terminal-gate-02 passed before pilot-a2.

pilot-a2 succeeded in10.24s/512 actions,513 Raw boundaries,1024 controller steps and5120 physics steps. Measured success-boundary displacements at10.20/10.22/10.24s were14.930/19.046/19.997mm with hold counts1/2/3; no fall. Independent task/terminal/zero-force/zero-external-wrench checks, Raw/Canonical full-video validation and LeRobot0.3.3 first/last-row/RGB readback passed. Contact remains unknown diagnostic. The historical single train alias is only a technical-pilot transport convention, not a training split.

Two of at most3 pilot attempts were used; no further capture is running or scheduled. One technical pilot is delivered for user behavior review; batch generation is not authorized. No model cache/training/upload/commit/push. WAM v3 HEAD/status exactly match the pre-implementation snapshot. All current successful capture implementation hashes match source,13 RAMBO schema/profile files and original controller/PushBox task are unchanged. Source changes remain in RAMBO and isolated WAM v2 governance only.

Evidence: workspace runs/audit/v2/DATA-008/20260926T055824Z/acceptance.json, source-invariants.json, paths.json and pilot-review.html. CPU suite243 passed/1 skipped/1CUDA deselected; final affected tests recorded separately. RAMBO docs-check has two inherited broken overview links to WAM v2 files missing from current WAM v3; no v3 edits were made to repair them.
