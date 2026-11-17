# Demonstration synthesis

The QLM-Bench demonstrations were synthesized without teleoperation: a large multimodal model drafted a
reference trajectory of commands (push, press, lift, kick) or a high-level executor (the six articulated
tasks), a human reviewed it, it was retargeted to randomized scenes and executed by the RAMBO controller in
MuJoCo (physics only), and only successful traces were kept and rendered into LeRobot v2.1 episodes.

What this repository releases:

- `src/qlm_bench/synthesis/references/`: the approved executors and recipes of the six articulated tasks
  (`approved-six-task-bindings.json` with executor, recipe, scope, horizon and the reference start state), and
  the approved reference traces / template of push_box, press_button, lift_basket and kick_ball_to_goal.
- `src/qlm_bench/synthesis/`: the executor libraries (template retargeting, smoothed press/lift/kick
  references, geometric experts), physics-trace recording and verification (`trace.py`, `quality.py`), and the
  offline audit of an articulated-task trace (`audit.py`).
- `example_one_demonstration.py`: re-generates one demonstration physics trace with the approved executor of an
  articulated task on a Standard100 scene, using the horizon recorded in the binding, then audits it:

```bash
python scripts/synthesis/example_one_demonstration.py <resource_root> turn_valve-20261016-091 /tmp/valve-demo
```

Not released: the 100-episode campaign and pilot drivers. They need the scene-source assets and the pilot
records of the original campaigns, which are not public; the HF dataset is their product. Push and press (and
10 lift_basket episodes) ran MuJoCo physics on MJWarp (GPU); the other lift_basket episodes, kick and the six
articulated tasks ran on native MuJoCo CPU. Standard100 always uses native CPU.

Settings: the bundled references are found automatically (`QLM_SYNTHESIS_REFERENCES` overrides);
`QLM_SYNTHESIS_WORKSPACE` points at external inputs that are not bundled (reference runs, scene sources),
which only the paths marked `@WORKSPACE@` in the bindings need.
