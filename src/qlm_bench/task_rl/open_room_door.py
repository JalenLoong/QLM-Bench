"""open_room_door additions to the Task RL scene worker: rollout-state capture/restore and five pure-read
columns. Every other task goes through the plain snapshot functions.

State. ``task_rl.snapshot.capture`` copies every task field not in ``TASK_EXCLUDE``; for the door that includes
``criteria`` (one ``DoorSocketExit`` per world, each holding the 110.8 MB MjModel), which ``torch.save`` pickles and the
``weights_only`` load refuses, so a door state could be written but never read back. ``capture`` leaves ``criteria`` out
for the door only (the task part keeps body, hold, task and the ``unlocked`` mirror); ``restore`` then sets every live
criterion's sticky flag from the restored mirror. The flag must be set: the worker reuses one runtime per scene and
``restore`` never calls ``task.reset()``, so a flag left True by the previous candidate would otherwise leak into the next
one. At every chunk boundary the mirror and the criterion's flag are equal (both change only in ``condition()`` and
``reset()``).

Columns (door only, appended after the common privileged columns; records only, not used by any reward):
    lever_rad, bolt_retraction_m, socket_exit_clearance_m   the predicate's own quantities (as ``DoorSocketExit.observe``)
    unlocked                                                the criterion's sticky unlock flag, read, never written
    fl_handle_contact                                       FL foot geom in contact with the ``<door>_handle`` geom
All are reads of the derived state after the command; ``observe()`` (which writes the sticky flag) is never called here.
"""
import contextlib

TASK = 'open_room_door'
COLUMNS = ['lever_rad', 'bolt_retraction_m', 'socket_exit_clearance_m', 'unlocked', 'fl_handle_contact']


def is_door(rt):
    return rt.task.task == TASK


@contextlib.contextmanager
def _criteria_excluded():
    from qlm_bench.task_rl import snapshot
    plain = snapshot.TASK_EXCLUDE
    snapshot.TASK_EXCLUDE = plain | {'criteria'}
    try:
        yield
    finally:
        snapshot.TASK_EXCLUDE = plain


def capture(rt):
    """``snapshot.capture``; for the door without the ``criteria`` objects."""
    from qlm_bench.task_rl import snapshot
    if not is_door(rt):
        return snapshot.capture(rt)
    with _criteria_excluded():
        return snapshot.capture(rt)


def restore(rt, state):
    """``snapshot.restore``; for the door the sticky unlock flag of every criterion is rebuilt from the restored mirror."""
    from qlm_bench.task_rl import snapshot
    if is_door(rt) and 'criteria' in state['parts']['task']:
        raise ValueError('Door state with pickled criteria objects')
    receipt = snapshot.restore(rt, state)
    if is_door(rt):
        for criterion, flag in zip(rt.task.criteria, rt.task.unlocked):
            criterion.unlocked = bool(flag)
    return receipt


def values(rt):
    """The five door columns of world 0 (pure reads)."""
    m, d = rt.physics.model, rt.physics.data[0]
    criterion = rt.task.criteria[0]
    prefix = criterion.profile['lever_joint'].removesuffix('_lever_joint')
    handle, foot = int(m.geom(prefix + '_handle').id), int(rt.physics.foot_geom_ids[0])
    touch = any({int(c.geom[0]), int(c.geom[1])} == {handle, foot} for c in d.contact[:d.ncon])
    world = criterion.local_corners @ d.geom_xmat[criterion.shaft].reshape(3, 3).T + d.geom_xpos[criterion.shaft]
    local = (world - d.xpos[criterion.frame]) @ d.xmat[criterion.frame].reshape(3, 3)
    return [float(d.qpos[criterion.address['lever_joint']]), float(d.qpos[criterion.address['bolt_joint']]),
            float(local[:, 1].min() - criterion.mouth_y), float(bool(criterion.unlocked)), float(touch)]
