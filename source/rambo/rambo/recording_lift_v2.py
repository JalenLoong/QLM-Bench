"""Compatibility name for the task-independent physical recorder."""
from .recording_v2 import Recorder


class LiftRecorder(Recorder):
    pass
