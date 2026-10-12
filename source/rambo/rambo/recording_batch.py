"""Indexed recorder fan-out at the same QP hooks; no lifecycle/reset ownership."""
from __future__ import annotations


class BatchRecorderMux:
    def __init__(self, environment, recorders):
        if len(recorders) != environment.num_envs or any(r.env is not environment or r.index != i for i, r in enumerate(recorders)):
            raise ValueError('Exactly one indexed recorder for each environment required')
        self.env = environment
        self.recorders = tuple(recorders)

    def before_control(self, action):
        for recorder in self.recorders:
            recorder.before_control(action)

    def after_physics(self, force, torque):
        for recorder in self.recorders:
            recorder.after_physics(force, torque)

    def after_control(self):
        for recorder in self.recorders:
            recorder.after_control()

    def before_reset(self, ids):
        for index in ids.tolist():
            self.recorders[index].before_reset(ids)

    def submit(self, commands):
        for recorder, command in zip(self.recorders, commands):
            if recorder.active and command is not None:
                recorder.submit(command)

    def capture_boundary(self):
        return [recorder.capture_boundary() if recorder.active else None for recorder in self.recorders]
