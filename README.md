# QLM-Bench

QLM-Bench provides Isaac quadrupedal loco-manipulation tasks, demonstrations and
policy-independent evaluation infrastructure. Its current tasks are **Push Box,
Lift Basket and Press Button**, using Go2, one FL manipulation leg, the original
RAMBO controller, native9 commands and ego/task RGB.

WAM-Policy is a separate model-side consumer. Installing QLM, reading its Canonical
releases and using its runtime do not require a WAM checkout or its model stack.

## CPU installation and existing demonstrations

Python3.10 or later can install the lightweight core. Build/install only the reviewed
source or CPU wheel; the wheel contains no simulator, controller weights or large assets.

```bash
python -m pip install .
qlm catalog
qlm contract
qlm resolve-release DATA-006-20260916T075451Z
```

For Raw/Canonical conversion, validation and replay, install the data extra in a separate
CPU environment with `python -m pip install '.[data]'`. The data tools use explicit
ffmpeg/ffprobe paths. Simulator and CPU data environments can remain separate.

```python
from qlm_bench.data import resolve_release, CanonicalDataset
ref = resolve_release('DATA-006-20260916T075451Z')
data = CanonicalDataset(ref, '/path/to/fixed-hub-snapshot')
print(data.episodes('test'))
print(data.rows(data.episodes('test')[0]['episode_uid'], columns=['simulation_time_ns', 'action']))
```

Download the exact `ref.revision` and its explicit Canonical/release paths from
[dontKnow23456/QLM-Bench](https://huggingface.co/datasets/dontKnow23456/QLM-Bench).
The catalogue separates demonstrations, resources, cases and results; do not treat
all Parquet files as one training table. Canonical metadata/row inspection does not
start Isaac. Call the explicit payload validation API before asserting release integrity.

## Resources and pinned simulator

`qlm assets` lists stable resource identities, source hashes, complete reviewed file
inventories, physical metadata and redistribution status. Acquire an exact source
from its manifest and prepare it under an explicit resource root:

```bash
qlm prepare-asset cardboard-box-05 --source-root /path/to/acquired-box-files --resource-root /path/to/resources
qlm resolve-asset cardboard-box-05 --resource-root /path/to/resources
```

The controller resource references the original `model_2000.pt` with405D observation
and18D residual action; these dimensions are separate from native9. Resource preparation
copies verified bytes, without rebuilding collision geometry or changing mass/friction.
Asset payload publication depends on each resource's license and dependency evidence.

The supported simulator is Isaac Sim6.0.1 / Isaac Lab3.0 Beta2 Patch1 with the pinned
PhysX/controller environment. Use `scripts/setup_isaacsim60.sh` and its dependency locks,
with explicit `RAMBO_VENV` and `RAMBO_ISAACLAB_SOURCE`. The installer never installs WAM.
Do not upgrade the simulator, Torch or controller as part of interface adaptation.

## Generate demonstrations

Prepare the resources named by `configs/collection/<task>.json`. Public task profiles
contain portable asset IDs and the accepted physical/expert parameters. Collection
uses the same factory, fixed-controller execution, task evaluator and terminal snapshots
as evaluation; Recorder only observes events. No historical internal approval file is
required for the public workflow.

```bash
OMNI_KIT_ACCEPT_EULA=Y scripts/rambo/run60.sh -m qlm_bench.cli collect \
  --task push_box --profile configs/collection/push_box.json \
  --resource-root /path/to/resources --output-dir /path/to/new-attempt \
  --ffmpeg /path/to/ffmpeg --ffprobe /path/to/ffprobe \
  --data-python /path/to/cpu-data-env/bin/python \
  --episode-length-s 20 --seed 42 --viz none
```

Every attempt has its own output directory. Failed/error/partial attempts are preserved;
only successful, fully validated attempts are eligible demonstrations. Use
`--diagnostic-only` for engineering checks. Generation does not automatically publish
files or create a frozen release. `qlm data` exposes conversion, validation, merge and
replay; replay preserves existing media bytes.

## Policy interface and evaluation

The CPU `qlm_bench.policy_interface` supplies explicit observation profiles, native9
commands and execution acknowledgements. Policy-visible RGB/instruction/declared root
state/history are separated from controller and evaluator state. Only completed20ms
command intervals enter history. Requested values remain distinct from float32,
force-zero execution; EEF targets remain absolute.

Use `qlm_bench.evaluation` with explicit EvalCases, a declared protocol, a runtime factory
and an action provider. The Isaac adapter loads simulator code lazily and requires an
explicit case reconstruction callback. [The provider example](examples/policy_adapter/constant_native9.py)
is a local engineering fixture. Whole-trial outcomes, failures, errors, retries and
missing trials are checked before metrics or publication.

No formal suite/horizon/seed-count/aggregate is inferred from demonstration releases.
WAM live transport, learned-policy closed loop and formal benchmark scores are not
established by this refactor. See [current status](docs/current/overview.md).

## Compatibility, development and sources

Existing Raw/Canonical payloads, UIDs, splits, timestamps and terminal media remain
immutable. Frozen compatibility specs preserve the original RAMBO_Data identity.
Existing 12.5Hz mounted RGB reference: WAM retains factor-four model sampling and its
own VAE grouping; physical Raw/Canonical RGB remains50Hz. Observer25Hz is diagnostic.
Command/controller/physics rates remain50/100/500Hz.

First WAM v2/v3 input is still Push Box50/40-5-5, release DATA-006-20260916T075451Z at
4b5e0ed9aa04cbc1143774798f63171b27d838a7. Later Lift/Press releases do not expand that
experiment. Model caches, normalizers and checkpoints remain owned by WAM.

- [Architecture and public boundaries](docs/architecture.md)
- [Resource contracts](docs/assets.md)
- [Evaluation and completion rules](docs/evaluation.md)
- [Development/governance index](docs/INDEX.md)
- [Third-party sources and licenses](THIRD_PARTY_NOTICES.md)

The inherited RAMBO license and copyright notices remain in the repository. Asset and
dataset permissions are separate. No new authorship, paper or benchmark result is claimed.
