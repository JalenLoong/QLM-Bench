---
id: DATA-009
type: change
status: completed
source_map: []
---
# Lift the basket: accepted pilot and ten local demonstrations

User selected the existing OASIS basket and FL lifting under the handle. Success: actual transformed object geometry minimum worldZ at least0.02m above floor, robot not fallen, for3 consecutive50Hz policy ticks. No tilt gate and no contact gate; contact unknown/diagnostic. Text: Lift the basket.

First prepare actual asset geometry and three-view static coverage review; user must approve placement/coverage before task freeze or technical pilot. Static repositioned images are not executed lifting or success evidence. Preserve source basket mass/collisions/materials, original RAMBO checkpoint/controller, native origin, native9/zero desired force, fixed ego/task mounts, and observer diagnostic-only.

After review: implement an independent task profile/expert and task-specific recorder mapping, preserve core data contract and Push Box behavior. Verify actual terminal-before-reset/reset isolation, acquire one bounded technical pilot, then stop for user acceptance. Latest scope after accepted pilot: acquire10 local successful demonstrations with episode splits8/1/1 and only bounded XY variation. Limit attempts to3 per slot and20sim seconds each, stop on programming errors, preserve failures locally. No attachment constraints, teleport, object animation or external wrench in physical demonstration capture. This batch is local only; no Hugging Face upload, pilot/failure/quarantine publication or model caches. No automatic Git commit/push, training or AMD access.

RAMBO v2 owns data work. Preserve active DATA-008 Press Button changes. WAM active v3 is untouched; use existing isolated v2 authority checkout solely for shared registry and DATA009 work records. Any shared recorder changes must account for concurrent DATA008 work before editing.

## Progress
- [x] User confirmed asset/action, simple success and fifty-after-pilot target.
- [x] Produce asset/scene/three-view review and receive approval.
- [x] Task/control/recorder implementation and strict terminal checks.
- [x] One pilot and user acceptance.
- [x] Ten local successful demonstrations and final data acceptance; no publication.

Evidence: runs/audit/v2/DATA-009/20260926T060352Z

## Additional a4–a6 trials complete; pilot review pending

User authorized3 additional physical attempts and lowered success to whole-basket minimum clearance>=2cm, not fallen for3policy ticks. New profile lift-basket-v2-2, old6cm records unchanged. Initial settling cannot count as success. Body holds an earlier fixed position rather than chasing the object. Original controller/assets/cameras/force-zero remain unchanged; WAM v3 was not modified or invoked.

a4: physical success at17.06s/853actions, terminal clearance2.526cm, but no controlled lift-phase transition; not the preferred pilot. a5:20s failure, threading achieved at times but visibility checks prevented lift. a6: physical success at14.94s/747actions, terminal clearance3.300cm. Before lift at12.30s, the actual foot collision envelope rear cleared the handle far side by1.477cm (required0.8cm) and the entire foot plus upper handle contact region passed the ego projection check. Independent geometry/terminal, Raw/Canonical video/stream checks and real LeRobot0.3.3 first/last dualRGB/native9 reads passed;9 relatedCPU tests passed. No dummy terminal action.

Visibility is NOT fully solved: lower handle portions are cropped; only62.88% of lift command instants have foot+upper handle region simultaneously in the nominal frustum, and projection does not establish no occlusion. Actual screenshots show cropping during part of lift. The user must review a6 behavior and ego coverage before fifty demonstrations. Additional budget is exhausted; no a7 without authorization. No batch, model cache/training, upload or commit/push.

Evidence: runs/audit/v2/DATA-009/20260926T060352Z/far-body-retries/results.json. Successful diagnostic Canonical: data/lingbot_rambo/canonical/lerobot_v2_1/DATA-009-20260926T060352Z/pilot-a6. Mac portable replay: offline/Lift-Basket-DATA-009-a4-a6-offline.zip under audit root (9 embedded videos and actual a6 frames; no HTTP service needed). Runtime source frozen in implementation-a6; authoritative execution checkout remains repos/RAMBO_Data-v2-lift-basket.

## User accepted a6; immediate scope is ten local demonstrations

User explicitly accepted a6 and authorized10 successful Lift the basket demonstrations with small initial position randomization, kept local with no Hugging Face upload. This supersedes the earlier immediate50 target/publication intent. Keep a6 controller/expert/cameras/asset/orientation/height/2cm success/force-zero unchanged; only initial XY varies. Fixed generation seed900942, X within±1cm/Y within±0.5cm, runtime seed42.10 slots have predeclared8/1/1 episode splits and at most3 attempts; retries use predeclared narrower XY offsets. Preserve all failures; stop on programming errors. Every accepted demonstration must pass physical success, whole-foot threading before lift, terminal-before-reset and Raw/Canonical checks. Accepted partial ego cropping remains disclosed, not a new rejection gate. Pilot is not counted among10. No v3/model/cache/training work, external upload or commit/push.

Evidence: runs/audit/v2/DATA-009/20260926T060352Z/local-ten-20260926T130524Z

## Final local-ten acceptance (2026-09-30)

User accepted a6, then requested exactly10 local demonstrations and clarified ego visibility is diagnostic only. This supersedes the earlier50/implied-publication proposal. Collection is complete:10 successful demonstrations,7042 actions, whole-episode train8/validation1/test1. Durations13.54–14.94s. Only initialX within±1cm/Y within±0.5cm varies; asset/orientation/height/controller/cameras and2cm/not-fallen/3tick success remain fixed. All10 pass full-foot threading before controlled lift, pre-reset terminal isolation, Raw/Canonical/media validation and real LeRobot first/last row reads. Merge preserves source timestamps and byte-identical video/terminal media.

The first2 episodes retain the originally accepted a6 visibility-gated expert; the remaining8 remove visibility blocking per the user's clarification. Exact old/new implementation hashes are recorded and checked; no other expert parameter changes. Ego cropping is diagnostic and does not reject a demonstration. One user-pause interruption (lift_demo_05-a1) is preserved/excluded;05-a2 is the accepted replacement. There are no task-failure retries in the final batch. Pilots are not counted among10.

Data and evidence stay local. No HF upload, model cache/normalization fitting, training, commit/push or v3 modification. Runtime remains the isolated RAMBO v2 checkout; main RAMBO's earlier Lift drafts are not authoritative execution source and concurrent DATA008 work is preserved. This is technical/data acceptance, not a claim of statistical generalization or user review of every demonstration.

Evidence: runs/audit/v2/DATA-009/20260926T060352Z/local-ten-20260926T130524Z/acceptance.json and collection-paths.json. Canonical: data/lingbot_rambo/canonical/lerobot_v2_1/DATA-009-local-ten-20260926T130524Z/demonstrations. Local review: review.html under the batch evidence directory.
