---
id: CURRENT-PRESS-BUTTON-COLLECTION-V2
type: current
status: accepted
source_map: []
---

**Status interpretation:** the collection/pilot statements below describe their original acceptance. Later DATA-011 publication covers only the ten DATA-010 demonstrations; the DATA-008 pilot stays local/excluded. Neither batch enters first adaptation v2/v3 training/evaluation. See [publication scope](publication-v2.md).
# Local Press Button collection

## Local collection completed

All10 new demonstrations succeeded on their first attempts:5194 actions, durations8.84–12.82s, split8/1/1. Industrial/Emergency assets5/5; early-stop/baseline configurations5/5; red/blue/green/orange3/3/2/2. No retries or failed batch attempts. Accepted DATA008 pilot remains separate and diagnostic.

User explicitly rejected6mmhousing shift: backup normalized geometry was verified vertex-by-vertex, with no relative housing/collar translation. Industrial threshold12mm; Emergency10mm; both3policy ticks/notfallen. Full500Hz Emergency peaks remain below15.41746mm clearance (largest13.9543mm). The20mmjoint limit and other physical parameters are unchanged; high-level EEF displacement approach/hold avoids overshoot.

All per-episode behavior/terminal/Raw/Canonical/video checks passed. Merged source video and terminal images are byte-preserved, timestamps inherit source int64 simulation clock, and independent LeRobot0.3.3 first/last-row dualRGB reads passed for all10. Reference bodyX is frozen during pressing and reference extension respects46cm alongworldX relativebase. Actual early-stop terminal distances to the unpressed cap plane are44.05–44.57cm; baseline41.00–44.15cm. These are configured modes, with real tracking effects and some distance overlap disclosed, not retrospectively relabeled categories.

CPU suite245 passed/1 skipped/1CUDA deselected. Core13RAMBO schema/profile files, original controller and WAMv3 HEAD/workingtree are unchanged. No model cache, training, upload, commit or push. Latest user cancelled Mac offline packaging; only local preview generated at http://127.0.0.1:8773/index.html.

Evidence: workspace runs/audit/v2/DATA-010/20260926T073438Z/acceptance.json, collection-paths.json, no-housing-shift-proof.json, v3-final-unchanged.json and core-invariants.json. The inherited profile flag physically_executed_press=false originated in the static asset review; actual execution is governed by real capture/summary/physics/behavior evidence. Original source manifests are preserved rather than rewritten.

[Execution](../work/archive/DATA-010/plan.md). User behavior review can follow, but no more collection is implied.

Later DATA-011 publication of the ten demonstrations is verified at `05b09b89225759382e28bc3dc586f1cfb755a997`. The original collection-time local-only/no-upload receipt remains historical; first adaptation v2/v3 training/evaluation exclusion is unchanged.
