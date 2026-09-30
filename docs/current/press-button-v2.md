---
id: CURRENT-PRESS-BUTTON-V2
type: current
status: accepted
source_map: []
---

**Status interpretation:** the collection/pilot statements below describe their original acceptance. Later DATA-011 publication covers only the ten DATA-010 demonstrations; the DATA-008 pilot stays local/excluded. Neither batch enters first adaptation v2/v3 training/evaluation. See [publication scope](publication-v2.md).
# Press Button technical-pilot acceptance

## Technical pilot completed

After explicit asset approval, pilot-a1 completed20s with valid terminal/data recording but failed to press the button due to lateral base drift and EEF misalignment; preserved and excluded. Upper-level base-Y/yaw feedback, EEF alignment and bounded X hold corrected the behavior without changing reviewed assets, physical parameters, threshold or controller. Fresh terminal-gate-02 passed before pilot-a2.

pilot-a2 succeeded in10.24s/512 actions,513 Raw boundaries,1024 controller steps and5120 physics steps. Measured success-boundary displacements at10.20/10.22/10.24s were14.930/19.046/19.997mm with hold counts1/2/3; no fall. Independent task/terminal/zero-force/zero-external-wrench checks, Raw/Canonical full-video validation and LeRobot0.3.3 first/last-row/RGB readback passed. Contact remains unknown diagnostic. The historical single train alias is only a technical-pilot transport convention, not a training split.

Two of at most3 pilot attempts were used; no further capture is running or scheduled. One technical pilot is delivered for user behavior review; batch generation is not authorized. No model cache/training/upload/commit/push. WAM v3 HEAD/status exactly match the pre-implementation snapshot. All current successful capture implementation hashes match source,13 RAMBO schema/profile files and original controller/PushBox task are unchanged. Source changes remain in RAMBO and isolated WAM v2 governance only.

Evidence: workspace runs/audit/v2/DATA-008/20260926T055824Z/acceptance.json, source-invariants.json, paths.json and pilot-review.html. CPU suite243 passed/1 skipped/1CUDA deselected; final affected tests recorded separately. RAMBO docs-check has two inherited broken overview links to WAM v2 files missing from current WAM v3; no v3 edits were made to repair them.

Task semantics: [ADR-0011](../decisions/ADR-0011.md). Source execution: [DATA-008](../work/archive/DATA-008/plan.md).
