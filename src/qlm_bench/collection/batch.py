"""Pure orchestration of a same-task wave through explicit runtime/recorder hooks."""
from __future__ import annotations


def collect_wave(runtime, recorder_mux, *, prepare_command, max_actions, command_prefix):
    if type(max_actions) is not int or max_actions < 1:
        raise ValueError('Explicit positive wave budget required')
    env = runtime.base_env
    if any(env.lane_tick(i) != 0 for i in range(env.num_envs)):
        raise ValueError('Each wave lane must start at its own episode origin')
    for recorder in recorder_mux.recorders:
        recorder.begin()
    env._v2_recorder = recorder_mux
    try:
        for boundary in range(max_actions):
            experts = runtime.expert_commands()
            commands = []
            for index, (request, diagnostics) in enumerate(experts):
                if request is None:
                    commands.append(None)
                    continue
                command = prepare_command(request, f'{command_prefix}:{index}:{boundary}', env.lane_tick(index))
                command['extensions']['expert'] = diagnostics
                commands.append(command)
            recorder_mux.submit(commands)
            runtime.step(commands)
            recorder_mux.capture_boundary()
            if not any(env.lane_active):
                break
        # A budget exhausted without environment-owned terminal cannot become
        # an accepted demonstration; the caller reports/archives the attempt.
        return {'complete': all(not recorder.active and recorder.terminal is not None for recorder in recorder_mux.recorders),
                'lanes': [{'env_index': i, 'terminal_owned': recorder.terminal is not None,
                           'commands': len(recorder.commands), 'boundaries': len(recorder.boundaries)}
                          for i, recorder in enumerate(recorder_mux.recorders)]}
    finally:
        env._v2_recorder = None
