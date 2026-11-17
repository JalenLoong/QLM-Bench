# Leg-Manip baseline (general implementation)

A re-implementation of *Learning Visual Quadrupedal Loco-Manipulation from Demonstrations*
(He et al., 2024, [arXiv:2403.20328](https://arxiv.org/abs/2403.20328)) on the Unitree Go2 in MuJoCo
([mjlab](https://github.com/mujocolab/mjlab) / MuJoCo Warp). It has the four parts of the original method:

1. **Trajectory parameters** (`traj/`): a rational Bézier curve of the manipulating foot plus SLERP of the
   calf direction, packed into a 31-D vector (FL/FR flag, 6 control points, log weights, start/end direction).
2. **Low-level controller** (`tasks/track/`, `learning/`): PPO with a concurrent state estimator that tracks
   the foot trajectory while the other three legs walk; a Lift task serves as curriculum.
3. **Demonstrations** (`collect/`, `tasks/manip/`): object-frame expert trajectories executed by the frozen
   controller in parallel; successful episodes are recorded as point cloud (768 points, depth camera, FPS)
   + robot state + trajectory parameters (`demo_io.py`, zarr).
4. **Planner** (`planner/`): a 3D Diffusion Policy (DP3) that predicts trajectory parameters from point
   clouds; closed-loop evaluation runs the planner at 10 Hz and the controller at 50 Hz (`eval/`).

This directory ships the method with two example tasks of the original paper's task family,
`press_button` and `close_dishwasher`. **The adaptation to the ten QLM-Bench tasks (task definitions,
conversion of the QLM-Bench demonstrations, Standard100 evaluation entry point) is not included yet**; it
will be added when the collaborators merge it. Until then this code cannot reproduce the Leg-Manip row of
Table 1 of the WAM-Policy paper.

Differences from the original paper: Unitree Go2 instead of Aliengo; mjlab / MuJoCo Warp instead of Isaac
Gym; the depth camera sits on a CAD-modelled mount on the robot (below); reward terms added for the Go2
(`manip_foot_load`, `base_approach`, `ee_pos_fine`, `base_heading`, `base_heading_dir`).

## Installation

Python 3.12, Linux x86_64. The simulator parts need an NVIDIA GPU:

```bash
cd baselines/leg_manip
uv sync --frozen --extra sim          # torch 2.9 (CUDA 12.8), mjlab 1.6.0
```

The planner alone needs no simulator and runs on CUDA or ROCm: install the package without extras on top of
an existing PyTorch (`uv pip install -e .`).

## Pipeline

```bash
# 1. controller: the warm-start chain used for the baseline (Lift -> Track -> +heading -> +heading direction)
scripts/train_controller.sh leg-manip-ctrl
# 2. check the expert trajectories with the frozen controller
uv run lm-collect --task press_button --controller <ctrl.pt> --check-expert --num-envs 100 --max-rounds 1
# 3. collect 100 successful demonstrations per task (200 frames each)
uv run lm-collect --task press_button --controller <ctrl.pt> --num-demos 100
# 4. planner, three seeds; EMA exports at 50/75/100% of training
uv run lm-train-planner --data data/demos/press_button.zarr --seed 0     # also 1, 2
# 5. closed-loop evaluation (planner 10 Hz + controller 50 Hz); --expert gives the expert upper bound
uv run lm-eval --task press_button --controller <ctrl.pt> --planner outputs/planner/press_button/seed0/epoch0500
```

`lm-hub upload|download|download-dir` moves demonstrations and planner checkpoints through the Hugging Face
Hub (`--repo <your namespace>/<repo>`). W&B logging is off by default (enable with `--agent.logger wandb`, `--wandb-mode online`,
`WANDB_ENTITY`); nothing names an account by default. `scripts/slurm/train_planner.sbatch` is a generic Slurm
example for the planner (three seeds, one GPU each).

Controller warm-start chain (`scripts/train_controller.sh`): Lift curriculum 2000 iterations from scratch;
Track 6000 iterations from it with the policy noise reset to 0.5 and the two heading rewards off; 3000
iterations with `base_heading` (weight 0.5); 3000 iterations with `base_heading_dir` (weight 1.0, the default).
Behaviour gates (`python -m leg_manip.eval.lift`, `python -m leg_manip.eval.track`) check each stage.

## Robot model

`src/leg_manip/assets/go2/go2.xml` derives from MuJoCo Menagerie `unitree_go2` (commit f3b6013, meshes under the
Unitree BSD-3-Clause license in `assets/go2/LICENSE`) and adds a depth-camera mount modelled from a CAD
assembly: a back plate, post and arm (box collision geometry, 0.44 kg in total) carrying a D435-class camera.
The optical centre is at (0.3233, 0, 0.3282) m in the base frame, looking forward and 30.5° down
(direction (0.862, 0, -0.508)), vertical field of view 58°, rendered at 160×100. The fore-aft position is
uncertain by about ±5 cm.

## Smoke test

```bash
python scripts/smoke/planner_synthetic.py --out /tmp/legmanip-smoke --device cpu   # planner, no simulator
python scripts/check_manip_env.py                                                    # manipulation env (sim extra)
```

## Licenses

This directory is released under CC BY-NC 4.0, like the rest of QLM-Bench (see the top-level `LICENSE`).
`src/leg_manip/planner/dp3/` is vendored from [3D-Diffusion-Policy](https://github.com/YanjieZe/3D-Diffusion-Policy)
(commit 47385d9) under the MIT License (`planner/dp3/LICENSE`; modifications are listed in `planner/dp3/__init__.py`).
The Go2 meshes are BSD-3-Clause (Unitree Robotics, `src/leg_manip/assets/go2/LICENSE`).
