---
id: INFER-001
type: exec-plan
status: completed
namespace: adaptation-v2
source_map: []
---
# Synchronous online closed-loop inference

## Purpose and scope

Implement the user-requested Adaptation v2/v3 close-loop scheme: single environment,
synchronous physical time freeze while waiting, one16-command ordinary group,
actual RGB/state/execution feedback, explicit reset/terminal/error and retry semantics.
The two WAM branches remain independent. QLM owns physical protocol, transport and
execution; WAM owns formal inference loading, observation preprocessing, sampling/KV.
No training, new demonstrations, model/normalizer redesign, AMD access or publication.

## Milestones and progress

- [x] 2026-10-03: source baseline inspected; isolated worktree and Work ID established.
- [x] 2026-10-03: public live envelope frozen with both WAM branch owners; frozen2.0 messages reused.
- [x] Model-independent live bridge implemented; WAM sessions remain in separate consumers.
- [x] Targeted CPU tests, repo checks and actual bounded Isaac/tiny-model engineering checks; formal SFT gate recorded separately.
- [x] Formal checkpoint/deployment gates recorded separately from tiny/synthetic engineering evidence.

## Compatibility

Preserve native9 absolute FL targets, float32/force-zero execution,50/100/500Hz
command/controller/physics,50Hz rawRGB and12.5Hz model sampling. Cold start one true
sample; ordinary feedback samples80/160/240/320ms after chunk start. Only completed
commands enter history. Terminal tails never become complete groups. V3 measured10D
state retains root-link/xyzw/world-to-body/ground semantics. Preserve original artifacts,
source weights, existing checkpoint resume validators and v2/v3 training behavior.

## Evidence thresholds

Verify independent loader/provenance checks; fixed-seed sampler; observed versus
predicted/scratch KV including real eviction; stale/duplicate/conflicting messages;
streaming VAE/timeline parity; actual execution acknowledgements and terminal/reset.
Use the original native server/client as source reference. Formal rollout requires a
verified SFT checkpoint, real frozen encoders/normalizers and feasible hardware; do not
label synthetic/tiny/replay evidence as formal learned-policy closed-loop success.

## Recovery and decisions

Follow repo registry/index and this paired work record. Keep local evidence under
workspace runs/audit/close-loop-20261003. Source changes and commands bind actual
checkout paths. Store actual attempts only; no planned run manifests or W&B claims.
Source publication is outside this implementation request. Update discoveries and
outcomes here; archive only after contracted completion gates are accurately recorded.

## QLM progress and discoveries

- [x] Public localhost lossless RPC, retry/error caching, stale/conflict rejection and frame bounds.
- [x] Common synchronous physical driver and explicit Isaac client CLI; no physics calls while waiting.
- [x] Real command acknowledgements,16-command groups,4 capture points, terminal prefix and reset isolation.
- [x] Targeted live CPU/mock tests:11 passed; combined live/evaluation/resources suite66 passed, including two separate processes over localhost.
- [x] Actual Isaac/runtime integration: controlled source and both tiny WAM samplers with original frozen VAE; two episodes each.
- [x] Both original formal SFT policies connected to actual Isaac execution and true feedback.

The first socket test attempt failed under the filesystem/network sandbox (EPERM), with
6 non-socket tests passed. The same local-only suite outside that sandbox passed9 initial tests; final expanded suite passed66 tests.
No simulator or model dependency was needed. The existing low-level runtime auto-resets
after capturing terminal; the bridge uses the owned pre-reset snapshot and never queries
post-reset RGB as feedback for the terminated epoch. Full duplicate feedback retention is
bounded to two chunks, with older identities retained and expired retries rejected.

### Evidence and handoff

Source: qlm_bench.live modules and public `qlm live` entrypoint. CPU receipt: targeted
pytest suite; actual simulator/formal WAM execution remains pending and is not inferred.
No commit, push, upload, new demonstrations, training or AMD action was performed.

## Integrated real-runtime engineering evidence — 2026-10-03

shared v2 implementation is now wired through the same public live RPC and real Isaac/RAMBO
execution. Both WAM branches separately completed two episodes with actual frozen VAE,
original normalizers/prompt, and a deliberately random tiny Transformer: five chunks
and75confirmed commands per episode, with final11-command prefix and no padded tail.
All model/RPC waits retained the same physical/controller clock; measured feedback
returned before the next prediction, and episode reset cleared state. Window4 crossed
real inference eviction. This is engineering causal-chain evidence, not formal SFT
policy performance. Evidence: workspace runs/audit/close-loop-20261003/actual-engineering-closed-loop.json.

Formal v2 and v3 step1000 checkpoints have now been independently identified in
dontKnow23456/WAM-Policy at223634bc64bc225881de80c2ac6e38c1de713a93. The earlier v2
AMD-pending status is historical. Transformer payloads are downloading into a new
versioned model directory; formal load/VRAM/rollout remains pending until actual
weights and hardware gates pass. No optimizer, training or old artifact mutation.

## Download recovery and formal run preparation — 2026-10-03

The original download processes stopped with incomplete payloads. Actual host inventory
found v2 seven of eleven shards and v3 no complete shard. Continued the same pinned
HF revision with HTTP resume after releasing the interrupted Xet worker locks; no
complete payload, optimizer, source artifact or original normalizer was replaced.
`runs/audit/close-loop-20261003/formal-download-recovery.json` and the HTTP log preserve
the actual recovery. Formal GPU admission/rollout remains pending until all files arrive.
Both formal launch commands use explicit worktree imports, original cached prompt,
BF16, 5/10 full denoising steps, single-env synchronous execution, two 1.5s engineering
episodes and the unchanged physical predicates. No formal benchmark score is defined.

## Accepted completion — 2026-10-03

Both original formal step1000 SFT Transformers at HF revision
223634bc64bc225881de80c2ac6e38c1de713a93 passed strict inference inventory/provenance
and key/shape loading, then the same public transport and actual Isaac/RAMBO path.
Each branch completed two separate 1.5s engineering episodes: five predictions,
four complete true-feedback commits and75confirmed native9 commands per episode.
The final11-command prefix ended at timeout, with no padded feedback or unexecuted
suffix in history. All24RPC waits per branch froze physics/controller/time exactly.
Original frozen VAE/normalizers/prompt were used; v3 consumed measured root-link state.
Window8 physically evicted the oldest logical group in both episodes, then reset
restored initial context. The final receipt is workspace
runs/audit/close-loop-20261003/completion.json, with actual commands, config identities,
per-call latency, original provenance, GPU memory and separate evidence layers.

The verified shared16GB deployment uses Transformer CUDA BF16 and frozen VAE CPU BF16.
The first all-GPU-v2 attempt ran out of memory during Isaac initialization and executed
zero commands; its complete failure record remains in v2/formal-sft-r1. Passing source
and engineering runtime gates completes INFER-001. Sampled quality, task success rate,
comparative benefit and formal benchmark score remain unverified; no training, AMD
connection, new demonstrations or source/HF publication was performed. Both policy
services received intentional SIGINT after the completed physical client; their final
summaries confirm stopped state, no failed calls and no cleanup errors.
