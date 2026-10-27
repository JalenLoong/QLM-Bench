"""PPO + concurrent estimator configuration for the low-level controller."""

from __future__ import annotations

from dataclasses import dataclass, field

from mjlab.rl import RslRlModelCfg, RslRlOnPolicyRunnerCfg, RslRlPpoAlgorithmCfg


@dataclass
class EstimatorActorCfg(RslRlModelCfg):
    estimator_hidden_dims: tuple[int, ...] = (256, 128)
    estimator_target_set: str = "estimator_target"
    class_name: str = "leg_manip.learning.estimator:EstimatorActorModel"


@dataclass
class EstimatorPpoAlgorithmCfg(RslRlPpoAlgorithmCfg):
    estimator_learning_rate: float = 1e-3
    estimator_num_learning_epochs: int = 1
    class_name: str = "leg_manip.learning.estimator:PPOWithEstimator"


@dataclass
class TrackRunnerCfg(RslRlOnPolicyRunnerCfg):
    actor: EstimatorActorCfg = field(
        default_factory=lambda: EstimatorActorCfg(
            hidden_dims=(512, 256, 128),
            activation="elu",
            obs_normalization=True,
            distribution_cfg={
                "class_name": "GaussianDistribution",
                "init_std": 1.0,
                "std_type": "scalar",
            },
        )
    )
    critic: RslRlModelCfg = field(
        default_factory=lambda: RslRlModelCfg(
            hidden_dims=(512, 256, 128), activation="elu", obs_normalization=True
        )
    )
    algorithm: EstimatorPpoAlgorithmCfg = field(
        default_factory=lambda: EstimatorPpoAlgorithmCfg(
            value_loss_coef=1.0,
            use_clipped_value_loss=True,
            clip_param=0.2,
            entropy_coef=0.01,
            num_learning_epochs=5,
            num_mini_batches=4,
            learning_rate=1.0e-3,
            schedule="adaptive",
            gamma=0.99,
            lam=0.95,
            desired_kl=0.01,
            max_grad_norm=1.0,
        )
    )


def track_go2_runner_cfg() -> TrackRunnerCfg:
    # 3e9 steps (paper) / (4096 envs * 24 steps) ~= 30k iterations.
    return TrackRunnerCfg(
        obs_groups={
            "actor": ("actor",),
            "critic": ("critic",),
            "estimator_target": ("estimator_target",),
        },
        experiment_name="legmanip_track_go2",
        wandb_project="leg-manip",
        save_interval=500,
        num_steps_per_env=24,
        max_iterations=30_000,
    )
