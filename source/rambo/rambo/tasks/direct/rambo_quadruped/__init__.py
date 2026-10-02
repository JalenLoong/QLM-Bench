"""Current quadruped task registration; base locomotion is a controller diagnostic."""
from __future__ import annotations
import gymnasium as gym
from . import agents

_TASKS = (
    ("Isaac-RAMBO-Quadruped-Go2-v0", "qp_env", "QPEnv", "QPEnvCfg"),
    ("Isaac-RAMBO-Quadruped-Push-Box-V2-Go2-v0", "push_box_v2", "PushBoxV2Env", "PushBoxV2Cfg"),
    ("Isaac-RAMBO-Quadruped-Lift-Basket-Go2-v0", "lift_basket_v2", "LiftBasketV2Env", "LiftBasketV2Cfg"),
    ("Isaac-RAMBO-Quadruped-Press-Button-V2-Go2-v0", "press_button_v2", "PressButtonV2Env", "PressButtonV2Cfg"),
)
for task_id, module, environment, config in _TASKS:
    gym.register(id=task_id, entry_point=f"{__name__}.{module}:{environment}",
                 disable_env_checker=True,
                 kwargs={"env_cfg_entry_point": f"{__name__}.{module}:{config}",
                         "crl2_cfg_entry_point": f"{agents.__name__}:crl2_flat_ppo_cfg.yaml"})
