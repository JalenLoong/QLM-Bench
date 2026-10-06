---
id: INFER-001
type: change
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
- [ ] Public protocol and compatibility interface frozen.
- [x] Model-independent QLM live bridge and the separately owned WAM consumers implemented.
- [x] CPU/repo checks and actual formal-checkpoint engineering runtime passed.
- [x] Formal artifact/runtime gates and research limits recorded separately.

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
