# Third-party notices

QLM-Bench is released under CC BY-NC 4.0 (`LICENSE`). Components derived from third-party work and the
assets distributed with the QLM-Bench dataset are listed below with their licenses.

## Code

- **RAMBO** (whole-body controller). `src/qlm_bench/controllers/rambo/` is adapted from the RAMBO code of
  Jin Cheng, Dongho Kang, Gabriele Fadini, Guanya Shi and Stelian Coros, "RAMBO: RL-Augmented Model-Based
  Whole-Body Control for Loco-Manipulation", IEEE Robotics and Automation Letters, 2025
  (https://arxiv.org/abs/2504.06662; code https://github.com/catachiii/rambo, commit
  `6f6c87c614255a5ada063da40206a2fa67054cb6`), licensed under CC BY-NC 4.0. Changes: the controller, QP torque
  optimizer, contact scheduling, joint-position controller and actuator model were ported to standalone PyTorch
  running on CPU against MuJoCo state, with per-case random streams; the policy network architecture is unchanged.
- **Interface files shared with WAM-Policy.** `src/qlm_bench/contracts/command/` (spec and validation) and
  `src/qlm_bench/live/history.py` are shared with WAM-Policy (https://github.com/AIGeeksGroup/WAM-Policy) and come
  from the same authors; in WAM-Policy they are provided under Apache-2.0.
- **MuJoCo** (Apache-2.0), **PyTorch** (BSD-3-Clause), **qpth** (Apache-2.0) and the other Python dependencies are
  installed separately and keep their own licenses.
- `baselines/leg_manip/` contains vendored third-party code with its own license files (see that directory).

## Controller checkpoint (distributed with the QLM-Bench dataset)

- **RAMBO controller checkpoint** (`model_2000.pt`, iteration 2000): trained by the QLM-Bench authors with the
  RAMBO code (https://github.com/catachiii/rambo, commit `6f6c87c614255a5ada063da40206a2fa67054cb6`); CC BY-NC 4.0.
  sha256 `1cc5f68fe15e37ccabae26060d79a26a8c078ed465a81f6f729c2009b67ca706` (for reference; the code does not
  enforce it).

## Assets (distributed with the QLM-Bench dataset)

- **Unitree Go2** robot meshes: Unitree Robotics, BSD-3-Clause (`licenses/unitree-go2-BSD-3-Clause.txt`).
- **Basket** (lift_basket): derived from OASIS (TeleHuman, https://github.com/TeleHuman/OASIS), MIT License,
  Copyright (c) 2026 TeleHuman (`licenses/OASIS-MIT.txt`).
- **Cardboard boxes**: from `usd-cardboard-box-assets` by GitHub user 1057822006-svg
  (https://github.com/1057822006-svg/usd-cardboard-box-assets), CC BY 4.0, attributed as its README requests.
- **Industrial button**: by Mark (@mark_saba) on Sketchfab
  (https://sketchfab.com/3d-models/industrial-button-a7e7c1772d764c3b913cccac66932236), with embedded credits to
  Zeppelin (https://sketchfab.com/zeppelingames); CC BY 4.0.
- **Kick goal, fridge, oven, valve, drawer, door and sweep scenes, and the press wall**: parameterized MJCF authored
  for QLM-Bench; CC BY 4.0.
- **Robot camera mount**: CAD model provided by a project collaborator; CC BY 4.0.

Each scene pack on the dataset carries a `manifest.json` with its source and attribution.
