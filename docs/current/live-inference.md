---
id: CURRENT-LIVE-INFERENCE
type: current
status: accepted
related_work: [INFER-001]
source_map:
  - src/qlm_bench/live/transport.py
  - src/qlm_bench/live/protocol.py
  - src/qlm_bench/live/runner.py
  - src/qlm_bench/live/isaac.py
  - tests/qlm/test_live_inference.py
---
# Synchronous physical inference interface

`qlm_bench.live` supplies a single-environment localhost client and an independent
policy-process RPC server. WAM owns its model and preprocessing; QLM supplies raw
physical RGB, optional measured root-link state and actual native9 confirmations.
The fixed camera/action/timing profiles remain the frozen `contracts_v2` 2.0.0 bundle.
No latent, model cache, normalization or privileged task input crosses the interface.

## Public messages

`RPCClient.call(method,payload,request_id=...,session_id=...,episode_id=...,reset_epoch=...)`
and `RPCServer(handler,host='127.0.0.1',port=8765)` use `qlm-live-v1` envelopes. The
handler receives the complete request dictionary and returns a JSON-compatible result.

| Method | Payload | Result |
| --- | --- | --- |
| reset | `reset`: frozen ResetRequest; `observation`: live packet | policy status |
| predict | `observation_id`: current observed message | frozen ActionChunk |
| feedback | `ack`: frozen ExecutionAck; `observation`: packet or null; `terminal`: summary or null | policy status |
| end | `reason` | policy status |

A live packet is `qlm-live-observation-v1`: `observation` is the unchanged compatibility
Observation; `samples` contain `capture_tick`, `capture_sim_ns`, two `rgb` arrays,
`sensor_frame_ids` and optional `root_state`; `state_semantics` declares root-link,
xyzw quaternion, world velocities, body gravity and ground reference. Only the five
public root-state fields are admitted. The compatibility frame path is a logical
`rgb/<camera>/<epoch>-<tick>.rgb` identity; its SHA256 identifies the transported raw
RGB bytes, explicitly labelled `payload_encoding: raw-rgb8`, not an on-disk PNG.
Camera world pose is reconstructed from measured root-link pose and the frozen mount.

The wire is a bounded four-byte network-order length prefix followed by JSON. RGB uses
raw uint8 HWC bytes encoded in base64. It is lossless and never resized. The default
frame cap is64MiB and per-image cap8MiB. No pickle/object-array deserialization exists.
Only localhost addresses are allowed. Install the `live` optional extra for NumPy/Pillow;
ordinary QLM core and transport never load Torch, Isaac or a model package.

## Execution and recovery

Cold start consumes exactly one true sample at0ms. Each ordinary chunk has16 native9
commands held for20ms each. Observations are copied at80/160/240/320ms, without reusing
boundary frames. `SynchronousDriver` calls the existing `ControllerRuntime.step` only
while executing a chunk. Waiting for reset/predict/feedback/end never advances PhysX,
the RAMBO controller or simulation time; clock identity is checked around each request.

Commands retain requested/transformed/filtered/executed fields and float32/force-zero
semantics. Both the existing public ExecutionHistory and compatibility PolicyHistory
validate acknowledgements. Only completed intervals enter history. Any mid-chunk terminal
stops the suffix; partial/unused commands remain explicit in the ack. The environment's
pre-reset snapshot supplies terminal evidence even if the underlying env already reset.
Incomplete feedback is never padded or encoded as an ordinary group.

Same request identities replay cached success/failure results; conflicts and stale epochs
are rejected. Model failures poison the epoch until a new reset. Command identities are
reserved before side effects and never reexecuted. Full feedback is bounded to the most
recent two chunks; an expired response fails explicitly, preserving identity knowledge.
Timeout uses a configured bounded retry of exactly the same request. Unconfirmed execution
requires reset, never guessed continuation. A server process restart loses in-memory state;
the client stops rather than treating it as an implicit recovery.

## Local engineering entrypoint

Run the WAM service in its own interpreter, then use the pinned simulator environment:

```bash
export QLM_INFERENCE_ROOT="$WORKSPACE_ROOT/repos/QLM-Bench-inference"
"$QLM_INFERENCE_ROOT/scripts/rambo/run60.sh" -m qlm_bench.cli live \
  --profile "$QLM_INFERENCE_ROOT/configs/collection/push_box.json" \
  --resource-root "$QLM_RESOURCE_ROOT" --output-dir "$QLM_RUN_DIR" \
  --host 127.0.0.1 --port "$QLM_POLICY_PORT" \
  --instruction "$QLM_POLICY_INSTRUCTION" --session-id engineering-001 \
  --episodes 2 --max-groups 6 --episode-length-s 1.5 \
  --seed 42 --policy-seed 42 --include-root-state \
  --ground-z 0 --ground-reference push-box-v2-plane-world-z0 --viz none
```

Source the workspace's `workspace.env` first and select the existing verified
`QLM_RESOURCE_ROOT` plus a new `QLM_RUN_DIR`. Set `QLM_POLICY_PORT` to the launched
service's port (v2 default8765; v3 default8763), and `QLM_POLICY_INSTRUCTION` to the
exact instruction bound by its verified prompt embedding. The wrapper binds QLM,
RAMBO and CRL2 to this inference checkout and selects the pinned simulator interpreter.

`--include-root-state` is required for the v3 consumer. `--ground-z` and
`--ground-reference` declare the measured state's ground convention. Output is a new
local attempt plus JSONL execution/physical capture receipts. No new demonstration or
benchmark result is published. Engineering group bounds, policy seeds and episode time
are explicit; these are not a default formal evaluation protocol.

CPU tests cover two real processes over localhost, exact RGB roundtrip, two causally
connected mock physical chunks, subsequent reset, all wait clocks, duplicate/conflicting
and stale identities, bounded framing and terminal at partial/full intervals. Actual
Isaac plus formal WAM checkpoint execution has a separate evidence gate in the
[completed plan](../work/archive/INFER-001/plan.md).

## Historical numerical/controller evidence — visual gate failed

The original v2 and v3 full SFT step1000 checkpoints both completed the verified
command above with two separate episodes each. Every episode ran five groups and
75confirmed commands, including an11-command timeout tail. All48model/RPC waits
across both consumers left physics/controller/time unchanged; true four-point RGB
feedback returned before each next prediction. V3 measured state used root-link,
xyzw, world velocities and ground profile push-box-v2-plane-world-z0. Both sessions
exercised real window eviction and subsequent reset. Per-layer evidence and original
input identities: workspace runs/audit/close-loop-20261003/completion.json.

The earlier numerical-only RTX5070Ti deployment used the Transformer on CUDA/BF16
and frozen VAE on CPU/BF16. Subsequent inspection found invalid grey RGB; effective
scene visual acceptance is withdrawn. These1.5s trials validate clock/controller execution;
they all ended at timeout and do not establish task success, benchmark score or
real-time operation. Original task/controller/data/model semantics remain unchanged.

## Historical visual gate correction — SIM-002 / 2026-10-03

Visual inspection of EVAL-002 found almost-uniform grey ego/task/observer camera
arrays. The earlier INFER-001 task-camera terminal SHA also matches uniform238
RGB. The numerical model/controller/clock/KV/reset evidence remains factual, but
valid scene visual feedback and effective visual closed-loop acceptance are
withdrawn for that original placement. The repair and ten-trial local evaluation
are now completed under shared-v2/SIM-002/EVAL-002 and v3/EVAL-001; see the accepted
local evaluation below. The invalid first batch is preserved and excluded as an infrastructure failure,
without selecting for policy success. Do not publish a success rate from grey-camera
trials. Diagnostic artifacts/preview are in runs/audit/push-box-first-sft-eval-20261003.

## Current visual deployment and evaluation

The accepted16GB deployment and complete local ten-trial results are in
[Push Box first-SFT evaluation](push-box-first-sft-evaluation.md). Use16 Transformer
blocks with CPU BF16 master parameters/CUDA forward plus the original VAE on CPU.
The earlier all-Transformer-GPU/VAE-CPU visual acceptance is withdrawn. Task metrics
apply to the declared nominal scene/seeds; formal benchmark/generalization claims
remain unavailable. Preserve invalid attempts and all first-attempt outcomes.
