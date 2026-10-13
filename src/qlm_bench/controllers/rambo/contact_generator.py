"""Numerical RAMBO implementation extracted from the retained source; no simulator imports."""
import torch
import numpy as np
from . import math as math_utils
from .math import quat_error as rambo_quat_error, xyzw_to_wxyz
from .tensor import to_torch
class ContactGenerator:

    def __init__(self, env):
        self._env = env
        self._contact_sequence = self._env.cfg.contact_generator_config['contact_sequence']
        self._contact_feet = []
        self._contact_max_index = []
        self._contact_mode = {}
        self._contact_timing = {}
        self._contact_extra = {}
        for key, value in self._contact_sequence.items():
            self._contact_feet.append(key)
            self._contact_mode[key] = []
            self._contact_timing[key] = []
            self._contact_extra[key] = []
            self._contact_max_index.append(len(value))
            for i in range(len(value)):
                if value[i][0] in ['stance', 'phase', 'swing']:
                    if value[i][0] == 'stance':
                        self._contact_mode[key].append(1.0)
                    elif value[i][0] == 'phase':
                        self._contact_mode[key].append(0.0)
                    elif value[i][0] == 'swing':
                        self._contact_mode[key].append(-1.0)
                else:
                    raise ValueError('Invalid contact mode')
                self._contact_timing[key].append(value[i][1])
                self._contact_extra[key].append(value[i][2:])
        self._contact_mode = torch.tensor(np.array([*self._contact_mode.values()]), dtype=torch.float32, device=self._env.device)
        self._contact_timing = torch.tensor(np.array([*self._contact_timing.values()]), dtype=torch.float32, device=self._env.device)
        self._contact_timing_total = torch.sum(self._contact_timing, dim=1)
        self._contact_timing_percentage = self._contact_timing / self._contact_timing_total[:, None]
        self._contact_extra = torch.tensor(np.array([*self._contact_extra.values()]), dtype=torch.float32, device=self._env.device)
        self._contact_timing_cumsum = torch.cumsum(self._contact_timing, dim=1)
        self._contact_timing_cumsum_percentage = torch.cumsum(self._contact_timing_percentage, dim=1)
        self._contact_max_index = torch.tensor(self._contact_max_index, device=self._env.device)
        self._current_contact_mode = torch.ones(self._env.num_envs, self._env.num_feet, dtype=torch.float32, device=self._env.device)
        self._next_contact_mode = torch.ones(self._env.num_envs, self._env.num_feet, dtype=torch.float32, device=self._env.device)
        self._after_current_contact_mode = torch.zeros(self._env.num_envs, self._env.num_feet, dtype=torch.float32, device=self._env.device)
        self._until_next_contact_mode = torch.zeros(self._env.num_envs, self._env.num_feet, dtype=torch.float32, device=self._env.device)
        self._current_contact_timing = torch.zeros(self._env.num_envs, self._env.num_feet, dtype=torch.float32, device=self._env.device)
        self._current_contact_extra = torch.zeros(self._env.num_envs, self._env.num_feet, 3, dtype=torch.float32, device=self._env.device)
        self._current_contact_phase = torch.zeros(self._env.num_envs, self._env.num_feet, dtype=torch.float32, device=self._env.device)
        self._current_contact_state = torch.ones(self._env.num_envs, self._env.num_feet, dtype=torch.bool, device=self._env.device)
        self._time_since_reset = torch.zeros(self._env.num_envs, device=self._env.device, dtype=torch.float32)
        self.debug_vis = False
        self.contact_generator_vis_handle = None

    def reset_idx(self, env_ids):
        if len(env_ids) == 0:
            return
        self._time_since_reset[env_ids] = self._env.time_since_reset[env_ids]
        current_mode_index = torch.sum(self._time_since_reset[env_ids, None, None] >= self._contact_timing_cumsum[None, :] + 0.0001, dim=-1)
        previous_mode_index = current_mode_index - 1
        next_mode_index = torch.clip(current_mode_index + 1, max=self._contact_max_index[None, :] - 1)
        for i in range(self._env.num_feet):
            self._current_contact_mode[env_ids, i] = torch.index_select(self._contact_mode[i], 0, current_mode_index[:, i])
            self._current_contact_timing[env_ids, i] = torch.index_select(self._contact_timing[i], 0, current_mode_index[:, i])
            self._current_contact_extra[env_ids, i] = torch.index_select(self._contact_extra[i], 0, current_mode_index[:, i])
            self._next_contact_mode[env_ids, i] = torch.index_select(self._contact_mode[i], 0, next_mode_index[:, i])
            self._after_current_contact_mode[env_ids, i] = torch.where(previous_mode_index[:, i] < 0, self._time_since_reset[env_ids], self._time_since_reset[env_ids] - torch.index_select(self._contact_timing_cumsum[i], 0, torch.clip(previous_mode_index[:, i], min=0)))
            self._until_next_contact_mode[env_ids, i] = torch.index_select(self._contact_timing_cumsum[i], 0, current_mode_index[:, i]) - self._time_since_reset[env_ids]
            idx = self._current_contact_mode[env_ids, i] >= 0.5
            self._current_contact_phase[env_ids, i] = torch.where(idx, torch.ones_like(self._current_contact_phase[env_ids, i]), self._current_contact_phase[env_ids, i])
            self._current_contact_state[env_ids, i] = torch.where(idx, True, self._current_contact_state[env_ids, i])
            idx = self._current_contact_mode[env_ids, i] <= -0.5
            self._current_contact_phase[env_ids, i] = torch.where(idx, torch.zeros_like(self._current_contact_phase[env_ids, i]), self._current_contact_phase[env_ids, i])
            self._current_contact_state[env_ids, i] = torch.where(idx, False, self._current_contact_state[env_ids, i])
            idx = torch.logical_and(self._current_contact_mode[env_ids, i] < 0.5, self._current_contact_mode[env_ids, i] > -0.5)
            self._current_contact_phase[env_ids, i] = torch.where(idx, torch.remainder(self._after_current_contact_mode[env_ids, i] + self._current_contact_extra[env_ids, i, 0] * self._current_contact_extra[env_ids, i, 1], self._current_contact_extra[env_ids, i, 1]) / self._current_contact_extra[env_ids, i, 1], self._current_contact_phase[env_ids, i])
            self._current_contact_state[env_ids, i] = torch.where(torch.logical_and(idx, self._current_contact_phase[env_ids, i] < self._current_contact_extra[env_ids, i, 2]), True, self._current_contact_state[env_ids, i])
            self._current_contact_state[env_ids, i] = torch.where(torch.logical_and(idx, self._current_contact_phase[env_ids, i] >= self._current_contact_extra[env_ids, i, 2]), False, self._current_contact_state[env_ids, i])

    def update(self):
        self._time_since_reset = self._env.time_since_reset
        current_mode_index = torch.sum(self._time_since_reset[:, None, None] >= self._contact_timing_cumsum[None, :] + 0.0001, dim=-1)
        previous_mode_index = current_mode_index - 1
        next_mode_index = torch.clip(current_mode_index + 1, max=self._contact_max_index[None, :] - 1)
        for i in range(self._env.num_feet):
            self._current_contact_mode[:, i] = torch.index_select(self._contact_mode[i], 0, current_mode_index[:, i])
            self._current_contact_timing[:, i] = torch.index_select(self._contact_timing[i], 0, current_mode_index[:, i])
            self._current_contact_extra[:, i] = torch.index_select(self._contact_extra[i], 0, current_mode_index[:, i])
            self._next_contact_mode[:, i] = torch.index_select(self._contact_mode[i], 0, next_mode_index[:, i])
            self._after_current_contact_mode[:, i] = torch.where(previous_mode_index[:, i] < 0, self._time_since_reset, self._time_since_reset - torch.index_select(self._contact_timing_cumsum[i], 0, torch.clip(previous_mode_index[:, i], min=0)))
            self._until_next_contact_mode[:, i] = torch.index_select(self._contact_timing_cumsum[i], 0, current_mode_index[:, i]) - self._time_since_reset
            idx = self._current_contact_mode[:, i] > 0.5
            self._current_contact_phase[:, i] = torch.where(idx, torch.ones_like(self._current_contact_phase[:, i]), self._current_contact_phase[:, i])
            self._current_contact_state[:, i] = torch.where(idx, True, self._current_contact_state[:, i])
            idx = self._current_contact_mode[:, i] < -0.5
            self._current_contact_phase[:, i] = torch.where(idx, torch.zeros_like(self._current_contact_phase[:, i]), self._current_contact_phase[:, i])
            self._current_contact_state[:, i] = torch.where(idx, False, self._current_contact_state[:, i])
            idx = torch.logical_and(self._current_contact_mode[:, i] < 0.5, self._current_contact_mode[:, i] > -0.5)
            self._current_contact_phase[:, i] = torch.where(idx, torch.remainder(self._after_current_contact_mode[:, i] + self._current_contact_extra[:, i, 0] * self._current_contact_extra[:, i, 1], self._current_contact_extra[:, i, 1]) / self._current_contact_extra[:, i, 1], self._current_contact_phase[:, i])
            self._current_contact_state[:, i] = torch.where(torch.logical_and(idx, self._current_contact_phase[:, i] < self._current_contact_extra[:, i, 2]), True, self._current_contact_state[:, i])
            self._current_contact_state[:, i] = torch.where(torch.logical_and(idx, self._current_contact_phase[:, i] >= self._current_contact_extra[:, i, 2]), False, self._current_contact_state[:, i])

    @property
    def desired_contact_state(self):
        return self._current_contact_state

    @property
    def desired_contact_phase(self):
        return self._current_contact_phase

    @property
    def desired_contact_mode(self):
        return self._current_contact_mode

    @property
    def desired_contact_mode_next(self):
        return self._next_contact_mode

    @property
    def until_next_contact_mode(self):
        return self._until_next_contact_mode

    @property
    def normalized_phase(self):
        contact_phase = self._current_contact_phase.clone()
        for i in range(4):
            idx = torch.logical_and(self._current_contact_mode[:, i] < 0.5, self._current_contact_mode[:, i] > -0.5)
            contact_phase[:, i] = torch.where(torch.logical_and(idx, self._current_contact_phase[:, i] < self._current_contact_extra[:, i, 2]), self._current_contact_phase[:, i] / self._current_contact_extra[:, i, 2], contact_phase[:, i])
            contact_phase[:, i] = torch.where(torch.logical_and(idx, self._current_contact_phase[:, i] >= self._current_contact_extra[:, i, 2]), (self._current_contact_phase[:, i] - self._current_contact_extra[:, i, 2]) / (1.0 - self._current_contact_extra[:, i, 2]), contact_phase[:, i])
        return contact_phase

    @property
    def stance_duration(self):
        stance_duration = self._current_contact_timing.clone()
        idx = self._current_contact_mode <= -0.5
        stance_duration = torch.where(idx, torch.zeros_like(stance_duration), stance_duration)
        idx = torch.logical_and(self._current_contact_mode < 0.5, self._current_contact_mode > -0.5)
        stance_duration = torch.where(idx, self._current_contact_extra[:, :, 1] * self._current_contact_extra[:, :, 2], stance_duration)
        return stance_duration
