---
id: DATA-009
type: exec-plan
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

## Static review ready

review-a1 completed with9 actual rendered coverage images, source hash check and original controller loading. This is static geometry/camera review, not real handle engagement or lifting success. Await user approval of asset/placement/coverage before task implementation or pilot. RAMBO docs-check reports two pre-existing cross-links into the active WAM-v3 checkout that lacks v2 pages; registry/governance and import boundaries pass. No source commit/push or collection.

Explicit user steering: do not modify v3 in any way. All DATA009 edits stay in RAMBO v2 and the isolated WAM v2 registry/work-record checkout; no v3 files/configs/branch/worktree changes or model pipeline execution.

Runtime isolation: after concurrent DATA008 changed recording_v2.py, a2 preflight refused source mismatch before simulator launch. New execution is in repos/RAMBO_Data-v2-lift-basket at unchanged base HEAD, with DATA009 additions only and a source-root assertion. Shared recorder changes are preserved, active WAMv3 untouched. Failed preflight is not a captured episode; only a1 has consumed a physical attempt so far.

## Pilot outcome: current budget exhausted

Asset/placement/camera review was explicitly approved. Three physical pilots each completed20s/1000actions and failed the unchanged6cm whole-mesh-clearance success. Post-settle maximum clearances: a1=0.003969m, a2=0.006491m, a3=0.011624m. Independent geometry/terminal checks passed on all3; no successful pilot or batch exists.7 relatedCPU tests pass. Source scale0.3 is included; convex-hull support vertices preserve exact rigid-mesh extrema under rotations.

a1 had body lateral/backward drift. a2 body position feedback improved tracking but lifted against the near side/shifted basket; a3 gated lift on measured insertion position and tracked the object, still resulting in pushing rather than stable lifting. Contact remains unknown; do not claim a resolved pair-contact/collision explanation. Stop at3 physical attempts; no auto-retry, no50batch, no upload/cache/training/commit/push. User must review results and authorize any further physical attempt budget.

One a2 startup was rejected BEFORE creating an episode/simulator because the shared recorder changed concurrently. It is a preflight rejection, not another physical attempt. Preserve DATA008 edits. Authoritative frozen Lift runtime now lives in repos/RAMBO_Data-v2-lift-basket, explicit entrypoint binding asserted; all v3 files/config/branch remain untouched. Earlier main-RAMBO DATA009 draft files are not the current runtime.

Evidence: runs/audit/v2/DATA-009/20260926T060352Z/pilot-results.json; pilots.html (3-view real execution), per-attempt behavior JSON and raw capture. Original failed videos keep.partial.mp4 naming but their encoders closed and media validation checks actual decoded counts. W&B results recorded offline after execution, explicitly labeled; no invented pre-execution logging.

## User-authorized additional attempts a4–a6

User explicitly grants3 more attempts, with body stopped farther back, ego visibility of foot/handle, and complete foot passage through handle before raising. Subsequent user instruction lowers minimum whole-mesh clearance to0.02m; not-fallen and3policy ticks retained. New task profile lift-basket-v2-2; old6cm records remain immutable and are not relabeled. Success is disabled during initial2.1s settling to avoid counting spawn clearance. Runtime remains isolated RAMBO v2; no v3 modifications. Foot passage uses actual source collision envelope beyond the handle far-side geometry, not just an EEF-center threshold. Ego frustum checks are diagnostic geometry and do not establish absence of occlusion; actual video remains necessary. Evidence under far-body-retries/.

## Additional a4–a6 trials complete; pilot review pending

User authorized3 additional physical attempts and lowered success to whole-basket minimum clearance>=2cm, not fallen for3policy ticks. New profile lift-basket-v2-2, old6cm records unchanged. Initial settling cannot count as success. Body holds an earlier fixed position rather than chasing the object. Original controller/assets/cameras/force-zero remain unchanged; WAM v3 was not modified or invoked.

a4: physical success at17.06s/853actions, terminal clearance2.526cm, but no controlled lift-phase transition; not the preferred pilot. a5:20s failure, threading achieved at times but visibility checks prevented lift. a6: physical success at14.94s/747actions, terminal clearance3.300cm. Before lift at12.30s, the actual foot collision envelope rear cleared the handle far side by1.477cm (required0.8cm) and the entire foot plus upper handle contact region passed the ego projection check. Independent geometry/terminal, Raw/Canonical video/stream checks and real LeRobot0.3.3 first/last dualRGB/native9 reads passed;9 relatedCPU tests passed. No dummy terminal action.

Visibility is NOT fully solved: lower handle portions are cropped; only62.88% of lift command instants have foot+upper handle region simultaneously in the nominal frustum, and projection does not establish no occlusion. Actual screenshots show cropping during part of lift. The user must review a6 behavior and ego coverage before fifty demonstrations. Additional budget is exhausted; no a7 without authorization. No batch, model cache/training, upload or commit/push.

Evidence: runs/audit/v2/DATA-009/20260926T060352Z/far-body-retries/results.json. Successful diagnostic Canonical: data/lingbot_rambo/canonical/lerobot_v2_1/DATA-009-20260926T060352Z/pilot-a6. Mac portable replay: offline/Lift-Basket-DATA-009-a4-a6-offline.zip under audit root (9 embedded videos and actual a6 frames; no HTTP service needed). Runtime source frozen in implementation-a6; authoritative execution checkout remains repos/RAMBO_Data-v2-lift-basket.

## User accepted a6; immediate scope is ten local demonstrations

User explicitly accepted a6 and authorized10 successful Lift the basket demonstrations with small initial position randomization, kept local with no Hugging Face upload. This supersedes the earlier immediate50 target/publication intent. Keep a6 controller/expert/cameras/asset/orientation/height/2cm success/force-zero unchanged; only initial XY varies. Fixed generation seed900942, X within±1cm/Y within±0.5cm, runtime seed42.10 slots have predeclared8/1/1 episode splits and at most3 attempts; retries use predeclared narrower XY offsets. Preserve all failures; stop on programming errors. Every accepted demonstration must pass physical success, whole-foot threading before lift, terminal-before-reset and Raw/Canonical checks. Accepted partial ego cropping remains disclosed, not a new rejection gate. Pilot is not counted among10. No v3/model/cache/training work, external upload or commit/push.

Evidence: runs/audit/v2/DATA-009/20260926T060352Z/local-ten-20260926T130524Z

User clarified ego visibility is only a heuristic suggestion, not a hard requirement. After the running bounded batch finishes, remove visibility gating from thread->lift, lift-progress pause and sequence acceptance; retain actual whole-foot threading/hold,2cm/not-fallen/3tick success, cameras, asset, controller and other a6 parameters. Existing accepted episodes remain valid; exact old/new expert hashes are allowlisted and recorded. No v3 changes.

## Paused by user

User requested pause. Collector and orchestration have exited.5 validated demonstrations are preserved; lift_demo_05-a1 was interrupted and has no summary.json, so it is not usable and must not be counted or overwritten. Preserve logs and the reported child exit code; the orchestration missing-summary exception followed the user interruption. No further collection/merge/upload until explicit user resume. Before resuming, reconcile this interrupted attempt and do not blindly rerun the old helper against its completed-stage record.

## Final local-ten acceptance (2026-09-30)

User accepted a6, then requested exactly10 local demonstrations and clarified ego visibility is diagnostic only. This supersedes the earlier50/implied-publication proposal. Collection is complete:10 successful demonstrations,7042 actions, whole-episode train8/validation1/test1. Durations13.54–14.94s. Only initialX within±1cm/Y within±0.5cm varies; asset/orientation/height/controller/cameras and2cm/not-fallen/3tick success remain fixed. All10 pass full-foot threading before controlled lift, pre-reset terminal isolation, Raw/Canonical/media validation and real LeRobot first/last row reads. Merge preserves source timestamps and byte-identical video/terminal media.

The first2 episodes retain the originally accepted a6 visibility-gated expert; the remaining8 remove visibility blocking per the user's clarification. Exact old/new implementation hashes are recorded and checked; no other expert parameter changes. Ego cropping is diagnostic and does not reject a demonstration. One user-pause interruption (lift_demo_05-a1) is preserved/excluded;05-a2 is the accepted replacement. There are no task-failure retries in the final batch. Pilots are not counted among10.

Data and evidence stay local. No HF upload, model cache/normalization fitting, training, commit/push or v3 modification. Runtime remains the isolated RAMBO v2 checkout; main RAMBO's earlier Lift drafts are not authoritative execution source and concurrent DATA008 work is preserved. This is technical/data acceptance, not a claim of statistical generalization or user review of every demonstration.

Evidence: runs/audit/v2/DATA-009/20260926T060352Z/local-ten-20260926T130524Z/acceptance.json and collection-paths.json. Canonical: data/lingbot_rambo/canonical/lerobot_v2_1/DATA-009-local-ten-20260926T130524Z/demonstrations. Local review: review.html under the batch evidence directory.
