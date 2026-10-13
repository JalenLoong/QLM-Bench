---
id: QLM-MUJOCO-PLATFORM-FEATURES
type: guide
status: active
source_map: []
---

# MuJoCo platform feature matrix

This is the QLM-SIM-005 local preparation matrix, not an AMD runtime acceptance.
Original CUDA/ROCm priorities and the Native rendering route remain unchanged.
Workspace evidence: `runs/audit/mujoco-alignment-repair-v1/`.

| Feature | Local evidence | Fixed ROCm candidate / required gate |
|---|---|---|
| Physics model and original assets | Original19-body Go2 and65/4/32 task convex hulls execute on Native/CUDA | Load the same portable resource manifests; reject any changed mesh/texture/profile |
| `put_model`, `make_data`, `get_data_into`, `reset_data` | Actual CUDA calls pass | Fixed AMD source has the required signatures, including world_id and reset mask; runtime smoke pending |
| Contact/constraint capacity | Explicit nconmax1024/njmax8192 for task packs; overflow fails | Candidate Data exposes naconmax/njmax; check actual counts and finite outputs on MI355X |
| Solver precision | CUDA float32 tolerance floor differs from Native float64; effective values recorded | Candidate has the same1e-6 floor; record effective values rather than only XML tolerance |
| Line-search budget | Profile's50 iterations retained | AMD fork otherwise caps HIP at10; adapter explicitly restores the model budget after put_model |
| Device aliases | Torch/Warp use cuda:N locally | Fixed ROCm Warp also exposes AMD devices as cuda:N; additionally require is_hip and expected GPU architecture |
| RNG | CPU generators per case and per sampling purpose; repeated reads/reset isolation tests | Same seed derivation and CPU sampling; HIP numeric/controller smoke still required |
| Graphs/BVH/batch renderer | No application-owned CUDA graph capture or GPU batch rendering required | Candidate documents unavailable HIP CUDA-graph/cuBQL/texture features; they are not pipeline prerequisites |
| Rendering | Native MuJoCo OSMesa and EGL actual fixtures; geometry matches | OSMesa is the common reference. Do not assume Instinct GPU OpenGL support |
| EGL admission | Press fixture passes; Box/Basket ROI thresholds fail, despite geometry and global metrics passing | Do not admit EGL for those production profiles. OSMesa collection/evaluation remains the approved route |
| WAM bridge | Original v3, three tasks×two episodes, actual RGB/state/terminal and96frozen RPC waits | Torch ROCm/model/VAE/DDP compatibility belongs to mandatory AMD smoke, not this local claim |

## Fixed source identities and preparation requirements

- MJWarp candidate: [AMD-Ecosystem/mujoco_warp at9229bb9](https://github.com/AMD-Ecosystem/mujoco_warp/tree/9229bb9d1a698c9464df862a915b46899720338c).
  Its pyproject declares3.8.1, Python>=3.10 and MuJoCo>=3.8.0. It deliberately
  does not install NVIDIA-only PyPI warp-lang. Keep this separate from the local
  CUDA constraints; do not let a dependency resolver replace source-built ROCm Warp.
- Warp candidate: [ROCm/warp at9d0b6cf](https://github.com/ROCm/warp/tree/9d0b6cf6f02cb7a0367e7378b7908b97cbbe1755).
  This revision's README lists gfx942/MI325X. That is not proof of MI355X support.
  Its build entry exposes `--hip-arch`; MI355X requires an explicit gfx950 target,
  confirmed by [AMD's ROCm7.1 compatibility matrix](https://rocm.docs.amd.com/en/docs-7.1.0/compatibility/compatibility-matrix.html).
  Build, kernel launch and actual architecture verification remain AMD smoke gates.
- Read-only downloads, hashes and API inspection are preserved under
  `rocm-source-api-inspection-a01` and `a02`. No ROCm library was installed locally,
  and no connection or job was submitted to the AMD server.
- OSMesa must be installed/built for the target OS ABI. The locally extracted Ubuntu
  library is local evidence, not a portable binary promise for an unknown target OS.

## Fail-closed handoff requirements

Before any downstream formal job can proceed, its smoke receipt must establish
the exact source/resource/environment identities, HIP/gfx950 execution, original
controller finite/no-fall/contact/reset behavior, matching recorded solver budget,
OSMesa fixed-state visual gate, actual data/VAE/proprioception readback and model
inference/training/checkpoint round trip. Missing/not_run/failed gates must not be
interpreted as success. There is no implicit switch to Native physics. P6 owns the
final administrator Slurm bundle and training budget; this P0–P2 matrix does not
claim that bundle has already been executed or fully prepared.
