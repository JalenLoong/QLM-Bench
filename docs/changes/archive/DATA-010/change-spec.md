---
id: DATA-010
type: change
status: completed
source_map: []
---
# Local randomized Press Button demonstrations

User approved10 new demonstrations, local-only. Preserve accepted DATA008 pilot separately. No QLM-Bench upload/release, model caches/training, commit/push or WAM v3 changes. Asset counts Industrial/Emergency5/5; motion baseline/early_stop5/5; cap colors red/blue/green/orange3/3/2/2. Frontx=.56m,y=.08-.12m,z=.285-.315m; +X axis, no rotation. Wall1m wide,.6m tall,.025m thick, neutral unchanged color. Whole-episode split8/1/1, train4perasset, validationIndustrial/testEmergency.

Actual physical cap motion only;20mm travel,12mm threshold,3policy ticks,notfallen,contact unknown diagnostic. Keep controller/checkpoint/force-zero/cameras/coredata contract/timestamps/terminal-before-reset. Backupcap targetdiameter matches8.85cm baseline; preserve source/provenance; only cap base-color hues modified while wear/text/othermaps remain unchanged. Wall position follows actual source back bounds.

Early-stop gap .075/.070/.065m across at most3 attempts (baseline .055m). Freeze bodyXreference afterbraking; keep46cm EEFreference limit. No silent base creep toward target to substitute for extension. Record actual base and EEF behavior. Retry only prescribed pressduration/gap; asset/position/color/motion/split unchanged. Max20sim seconds perattempt; programerrors stop before retry. Failures retained, no replacing types/loweringcriteria. First early-stop and first backupasset are inspected immediately and count in10 ifpassed; no extra pilot batch.

Deliver local Raw/Canonical collection/split/provenance/distributions/behaviorchecks/LeRobotreadback, failures and Mac portable offline replay. Stop with specificshortfall ifbudgetexhausted. WAMv3 protected; existing Lift Basket work must be preserved.

## Progress
- [x] Backup asset structure, recolors and camera range verification.
- [x] Fixed seeded10-slot scenarios and bounded attempts.
- [x] Ten usable local demonstrations or explicit shortfall.
- [x] Local merged8/1/1 dataset, checks and offline replay.

Evidence: runs/audit/v2/DATA-010/20260926T073438Z

## User correction: asset-specific threshold

User rejected6mmhousing/collarshift. Preserve backup geometry; Emergency Stop Button episodes use10mm success threshold, Industrial remains12mm. Both retain3ticks/notfallen,20mmjointlimit and existing physical parameters. Measured-displacement upper-level EEF approach/hold targets11mm forEmergency to avoid collar penetration; no direct object manipulation or low-levelcontroller changes. Checks and metadata use the per-episode threshold, never assume12mm globally. Receipt: asset-clearance-resolution.json.

## Local collection completed

All10 new demonstrations succeeded on their first attempts:5194 actions, durations8.84–12.82s, split8/1/1. Industrial/Emergency assets5/5; early-stop/baseline configurations5/5; red/blue/green/orange3/3/2/2. No retries or failed batch attempts. Accepted DATA008 pilot remains separate and diagnostic.

User explicitly rejected6mmhousing shift: backup normalized geometry was verified vertex-by-vertex, with no relative housing/collar translation. Industrial threshold12mm; Emergency10mm; both3policy ticks/notfallen. Full500Hz Emergency peaks remain below15.41746mm clearance (largest13.9543mm). The20mmjoint limit and other physical parameters are unchanged; high-level EEF displacement approach/hold avoids overshoot.

All per-episode behavior/terminal/Raw/Canonical/video checks passed. Merged source video and terminal images are byte-preserved, timestamps inherit source int64 simulation clock, and independent LeRobot0.3.3 first/last-row dualRGB reads passed for all10. Reference bodyX is frozen during pressing and reference extension respects46cm alongworldX relativebase. Actual early-stop terminal distances to the unpressed cap plane are44.05–44.57cm; baseline41.00–44.15cm. These are configured modes, with real tracking effects and some distance overlap disclosed, not retrospectively relabeled categories.

CPU suite245 passed/1 skipped/1CUDA deselected. Core13RAMBO schema/profile files, original controller and WAMv3 HEAD/workingtree are unchanged. No model cache, training, upload, commit or push. Latest user cancelled Mac offline packaging; only local preview generated at http://127.0.0.1:8773/index.html.

Evidence: workspace runs/audit/v2/DATA-010/20260926T073438Z/acceptance.json, collection-paths.json, no-housing-shift-proof.json, v3-final-unchanged.json and core-invariants.json. The inherited profile flag physically_executed_press=false originated in the static asset review; actual execution is governed by real capture/summary/physics/behavior evidence. Original source manifests are preserved rather than rewritten.
