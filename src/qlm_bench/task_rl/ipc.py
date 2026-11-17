"""Length-prefixed JSON frames between the Task RL scene worker and its client.

Each frame is a 4-byte big-endian length followed by a `qlm_bench.live.transport` JSON payload. The
worker writes frames to a private copy of its stdout pipe so that C-level prints reach stderr.
"""
import math
import os
import struct
import sys

from qlm_bench.live.transport import dumps, loads, MAX_FRAME_BYTES


def read_frame(stream):
    header=stream.read(4)
    if not header:return None
    if len(header)!=4:raise EOFError('Incomplete IPC header')
    count=struct.unpack('!I',header)[0]
    if not 0<count<=MAX_FRAME_BYTES:raise ValueError('IPC frame bound exceeded')
    payload=bytearray()
    while len(payload)<count:
        block=stream.read(count-len(payload))
        if not block:raise EOFError('Incomplete IPC payload')
        payload.extend(block)
    return loads(bytes(payload))


def write_frame(stream,value):
    raw=dumps(value)
    if len(raw)>MAX_FRAME_BYTES:raise ValueError('IPC response bound exceeded')
    stream.write(struct.pack('!I',len(raw)));stream.write(raw);stream.flush()


def task_progress(rt):
    """Finite task progress of the live state (push_box: box forward displacement in metres since reset)."""
    value=float(rt.outcome['progress'])
    if not math.isfinite(value):raise FloatingPointError('Nonfinite task progress')
    return value


def protocol_stdout():
    """Frames go to a private copy of the stdout pipe; fd 1 then points at stderr, so C-level
    prints (libmujoco WARNING, Mesa) reach the worker log instead of the frame stream."""
    sys.stdout.flush()
    channel=os.fdopen(os.dup(1),'wb')
    os.dup2(2,1)
    return channel
