---
id: QLM-DATA-012
type: exec-plan
status: completed
related_work: [QLM-DATA-012, v2/DATA-014, v3/DATA-004]
source_map: []
---
# Policy RGB 640×360

User-authorized spatial-only reduction on 2026-10-14. Preserve historical 720p hashes/assets/data/checkpoints. Policy RGB/action 50 Hz; RAMBO 100 Hz; physics 500 Hz; Observer 720p/25 Hz. Intrinsics half; mounts/FoV unchanged. V2 video/action and v3 video/10D/action remain separate. No formal collection/training/AMD/publication/commit/push.

## Progress

- Source/dirty-state baseline captured.
- Completed: versioned camera/data/preprocessing identities; separate v2/v3 reader/cache/SFT/live adaptation.
- Completed: actual same-state OSMesa coverage,101-action MJWarp diagnostic export, both actual frozen VAE/SFT/online readbacks and strict original step1000 model reset commits; old/new EvalCase reconstruction; frozen specs and ten historical720p payload inventories verified.

## Acceptance

640×360 dual RGB at 50 FPS; identical normalized frustum; Observer unchanged; N+1 Raw/N Canonical and terminal pass; both actual VAE outputs [B,48,T,24,20]; v3 10D timestamps unchanged; old cache identity rejected for new profile and old profiles remain accepted. Distinguish input compatibility from unmeasured policy performance.

## Discoveries / Decision Log

V2/v3 have independently maintained video/reader/runtime code. New explicit spatial identities preserve byte-frozen historical specifications. Evidence: runs/audit/rgb-resolution-360p-20261014-v1/.

## Validation / Outcome

QLM114passed/13skipped plus final EvalCase subset9passed/3skipped; v2 make check131passed/20skipped; v3 make check59passed. New diagnostic real Raw101actions/102boundaries/1011physics boundaries. Both actual frozenVAE latents[1,48,7,24,20], online cold-start/four-sample feedback equal offline; v3 10D80ms/initial+4 alignment preserved. Both strict full step1000 checkpoint loads and actual360p session reset/backbone cache commits pass. New and legacy EvalCase each execute16stand commands/0.32s with correct resolution,terminal and media. No learned-policy task outcome/SR claim.

Evidence: workspace runs/audit/rgb-resolution-360p-20261014-v1/{completion.json,report.md,changed-files.json,review.html}. Failed/misconfigured early attempts remain separately recorded; final checks supersede only their own failures. Shared-v2 DATA014 is WAM-only; registry mirror is the original QLM shared authority; independent MuJoCo historical shared table remains unchanged.

## Boundaries / Recovery

No formal collection/training/AMD/remote mutation/commit/push; no weights or old dataset overwrite. Full-SFT historical50/40-5-5 admission remains fixed; future dataset release is not implicitly admitted. Old checkpoints retain training hash; runtime input SHA is separate. Use updatedQLM source and explicit online rgb_profile; historical wheel is not rebuilt. Existing10formal720p pilots remain pending review. All task-start dirty work retained.
