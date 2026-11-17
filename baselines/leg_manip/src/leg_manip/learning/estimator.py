"""Concurrent state estimator for the low-level controller.

Paper Sec. IV-B: the actor additionally receives "the robot's velocity and the
positions of the end-effector as predicted by the state estimator [Ji et al. 2022].
This estimator takes the same 15-timesteps history observation as its input."

- :class:`EstimatorActorModel`: rsl_rl MLP actor with an estimator head. The
  estimate is concatenated to the (normalized) actor observation; its gradient is
  stopped so PPO does not shape the estimator.
- :class:`PPOWithEstimator`: PPO that, before each policy update, regresses the
  estimator onto the ``estimator_target`` observation group with its own optimizer.
"""

from __future__ import annotations

import copy
import math

import torch
import torch.nn as nn
from rsl_rl.algorithms import PPO
from rsl_rl.models import MLPModel
from rsl_rl.modules import MLP
from tensordict import TensorDict

OBSERVATION_CONTRACT_VERSION = 2
"""Version 2 uses heading-frame x/y and environment-absolute z for foot positions."""


class EstimatorActorModel(MLPModel):
    def __init__(
        self,
        obs: TensorDict,
        obs_groups: dict[str, list[str]],
        obs_set: str,
        output_dim: int,
        hidden_dims: tuple[int, ...] | list[int] = (512, 256, 128),
        activation: str = "elu",
        obs_normalization: bool = False,
        distribution_cfg: dict | None = None,
        estimator_hidden_dims: tuple[int, ...] | list[int] = (256, 128),
        estimator_target_set: str = "estimator_target",
    ) -> None:
        self.estimator_target_groups = list(obs_groups[estimator_target_set])
        self.estimate_dim = sum(obs[g].shape[-1] for g in self.estimator_target_groups)
        super().__init__(
            obs,
            obs_groups,
            obs_set,
            output_dim,
            hidden_dims,
            activation,
            obs_normalization,
            distribution_cfg,
        )
        self.estimator = MLP(
            self.obs_dim, self.estimate_dim, estimator_hidden_dims, activation
        )
        self.register_buffer(
            "observation_contract_version",
            torch.tensor(OBSERVATION_CONTRACT_VERSION, dtype=torch.int64),
        )

    def load_state_dict(self, state_dict, strict: bool = True, assign: bool = False):
        """Reject incompatible observation semantics before copying any weights.

        Both inference and PPO resume load the actor through this method. A
        non-strict load may ignore parameter keys, but cannot bypass this contract.
        """
        version = state_dict.get("observation_contract_version")
        if (
            not isinstance(version, torch.Tensor)
            or version.shape != torch.Size([])
            or version.dtype != torch.int64
            or version.item() != OBSERVATION_CONTRACT_VERSION
        ):
            raise RuntimeError(
                "Incompatible controller observation contract: expected version "
                f"{OBSERVATION_CONTRACT_VERSION} (environment-absolute foot height). "
                "Retrain the controller; unversioned/base-relative checkpoints "
                "cannot be reused."
            )
        return super().load_state_dict(state_dict, strict=strict, assign=assign)

    def _get_latent_dim(self) -> int:
        return self.obs_dim + self.estimate_dim

    def get_latent(self, obs, masks=None, hidden_state=None) -> torch.Tensor:
        x = super().get_latent(obs, masks, hidden_state)
        return torch.cat([x, self.estimator(x).detach()], dim=-1)

    def estimator_loss(self, obs: TensorDict) -> torch.Tensor:
        x = super().get_latent(obs)
        target = torch.cat([obs[g] for g in self.estimator_target_groups], dim=-1)
        return (self.estimator(x) - target).square().mean()

    def as_jit(self) -> nn.Module:
        return _ExportEstimatorActor(self)

    def as_onnx(self, verbose: bool) -> nn.Module:
        return _ExportEstimatorActor(self)


class _ExportEstimatorActor(nn.Module):
    """Deterministic actor with the estimator folded in, for ONNX / JIT export."""

    is_recurrent: bool = False

    def __init__(self, model: EstimatorActorModel) -> None:
        super().__init__()
        self.obs_normalizer = copy.deepcopy(model.obs_normalizer)
        self.estimator = copy.deepcopy(model.estimator)
        self.mlp = copy.deepcopy(model.mlp)
        assert model.distribution is not None
        self.deterministic_output = model.distribution.as_deterministic_output_module()
        self.input_size = model.obs_dim

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.obs_normalizer(x)
        x = torch.cat([x, self.estimator(x)], dim=-1)
        return self.deterministic_output(self.mlp(x))

    @torch.jit.export
    def reset(self) -> None:
        pass

    def get_dummy_inputs(self) -> tuple[torch.Tensor]:
        return (torch.zeros(1, self.input_size),)

    @property
    def input_names(self) -> list[str]:
        return ["obs"]

    @property
    def output_names(self) -> list[str]:
        return ["actions"]


class PPOWithEstimator(PPO):
    actor: EstimatorActorModel

    def __init__(
        self,
        *args,
        estimator_learning_rate: float = 1e-3,
        estimator_num_learning_epochs: int = 1,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.estimator_num_learning_epochs = estimator_num_learning_epochs
        self.estimator_optimizer = torch.optim.Adam(
            self._raw_actor.estimator.parameters(), lr=estimator_learning_rate
        )

    def update(self) -> dict[str, float]:
        est_loss = self._update_estimator()
        loss_dict = super().update()
        loss_dict["estimator"] = est_loss
        return loss_dict

    def _update_estimator(self) -> float:
        estimator = self._raw_actor.estimator
        total, count = 0.0, 0
        generator = self.storage.mini_batch_generator(
            self.num_mini_batches, self.estimator_num_learning_epochs
        )
        for batch in generator:
            loss = self._raw_actor.estimator_loss(batch.observations)
            self.estimator_optimizer.zero_grad()
            loss.backward()
            if self.is_multi_gpu:
                grads = [p.grad.view(-1) for p in estimator.parameters()]
                flat = torch.cat(grads)
                torch.distributed.all_reduce(flat, op=torch.distributed.ReduceOp.SUM)
                flat /= self.gpu_world_size
                offset = 0
                for p in estimator.parameters():
                    n = p.numel()
                    p.grad.copy_(flat[offset : offset + n].view_as(p.grad))
                    offset += n
            nn.utils.clip_grad_norm_(estimator.parameters(), self.max_grad_norm)
            self.estimator_optimizer.step()
            total += loss.item()
            count += 1
        return total / max(count, 1)

    def warm_start(self, loaded_dict: dict, noise_std: float | None) -> None:
        """Copy actor and critic from another stage's checkpoint, as a new run.

        Unlike resume, optimizer states and the iteration count stay fresh. A
        converged stage leaves little exploration noise; `noise_std` resets it.
        """
        self.load(loaded_dict, {"actor": True, "critic": True}, strict=True)
        if noise_std is None:
            return
        dist = self._raw_actor.distribution
        with torch.no_grad():
            if hasattr(dist, "std_param"):
                dist.std_param.fill_(noise_std)
            else:
                dist.log_std_param.fill_(math.log(noise_std))

    def save(self) -> dict:
        saved = super().save()
        saved["estimator_optimizer_state_dict"] = self.estimator_optimizer.state_dict()
        return saved

    def load(self, loaded_dict: dict, load_cfg: dict | None, strict: bool) -> bool:
        out = super().load(loaded_dict, load_cfg, strict)
        if (load_cfg is None or load_cfg.get("optimizer")) and (
            "estimator_optimizer_state_dict" in loaded_dict
        ):
            self.estimator_optimizer.load_state_dict(
                loaded_dict["estimator_optimizer_state_dict"]
            )
        return out
