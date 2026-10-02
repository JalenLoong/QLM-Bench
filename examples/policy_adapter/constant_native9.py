"""CPU engineering action provider example; never a learned policy or benchmark score."""
from qlm_bench.policy_interface import Native9Command


class ConstantNative9Provider:
    def __init__(self, command_values):
        self.command_values = tuple(command_values)
        self.counter = 0

    def reset(self, context):
        self.counter = 0

    def command(self, observation):
        self.counter += 1
        return Native9Command.from_values(self.command_values, episode_uid=observation.episode_uid,
                                         reset_epoch=observation.reset_epoch,
                                         command_id=f"constant/{self.counter}")
