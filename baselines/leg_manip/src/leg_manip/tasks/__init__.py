"""mjlab task registration (entry point group: mjlab.tasks)."""

from mjlab.rl import MjlabOnPolicyRunner
from mjlab.tasks.registry import register_mjlab_task

from leg_manip.learning.runner import ControllerRunner
from leg_manip.tasks.manip.env_cfg import make_manip_env_cfg
from leg_manip.tasks.manip.specs import TASKS
from leg_manip.tasks.track.env_cfg import make_track_env_cfg
from leg_manip.tasks.track.rl_cfg import track_go2_runner_cfg

register_mjlab_task(
    task_id="LegManip-Track-Go2",
    env_cfg=make_track_env_cfg(),
    play_env_cfg=make_track_env_cfg(play=True),
    rl_cfg=track_go2_runner_cfg(),
    runner_cls=ControllerRunner,
)

# Manipulation tasks reuse the tracking controller (same observation groups), so
# `play <task> --checkpoint-file <controller.pt>` runs the expert open-loop.
for _spec in TASKS.values():
    register_mjlab_task(
        task_id=_spec.task_id,
        env_cfg=make_manip_env_cfg(_spec),
        play_env_cfg=make_manip_env_cfg(_spec),
        rl_cfg=track_go2_runner_cfg(),
        runner_cls=MjlabOnPolicyRunner,
    )
