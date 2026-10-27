import numpy as np
import pytest
import torch
import zarr

from leg_manip.demo_io import write_zarr
from leg_manip.planner.dataset import DemoDataset
from leg_manip.planner.dp3 import LinearNormalizer
from leg_manip.planner.model import (
    PlannerModelCfg,
    build_policy,
    load_checkpoint,
    save_checkpoint,
)


def _episodes(n_ep: int = 3, t: int = 10, p: int = 16):
    eps = []
    for e in range(n_ep):
        frames = np.arange(t, dtype=np.float32) + 100 * e
        action = np.zeros((t, 31), dtype=np.float32)
        action[:, 0] = e % 2
        action[:, 1:19] = frames[:, None]
        action[:, 27] = action[:, 30] = -1
        eps.append(
            {
                "point_cloud": np.repeat(frames[:, None, None], p * 3, 1).reshape(
                    t, p, 3
                ),
                "state": np.repeat(frames[:, None], 17, 1),
                "action": action,
            }
        )
    return eps


def test_windows_pad_at_episode_edges(tmp_path):
    path = tmp_path / "demo.zarr"
    write_zarr(path, _episodes(), {"task": "unit"})
    ds = DemoDataset(
        path, horizon=4, n_obs_steps=2, n_action_steps=1, val_ratio=0.0, device="cpu"
    )
    # pad_before = 1, pad_after = 0 -> per episode: t - horizon + 1 + pad_before.
    assert len(ds.train_index) == 3 * (10 - 4 + 1 + 1)
    batch = ds.batch(ds.train_index[:1])
    # First window starts one step before the episode: obs repeats frame 0.
    assert batch["obs"]["agent_pos"][0, :, 0].tolist() == [0.0, 0.0]
    assert batch["action"][0, :, 1].tolist() == [0.0, 0.0, 1.0, 2.0]
    # No window crosses an episode boundary.
    for rows in ds.train_index:
        assert len({int(r) // 10 for r in rows}) == 1


def test_validation_split_is_by_episode(tmp_path):
    path = tmp_path / "demo.zarr"
    write_zarr(path, _episodes(n_ep=5), {"task": "unit"})
    ds = DemoDataset(
        path, horizon=4, n_obs_steps=2, n_action_steps=1, val_ratio=0.2, device="cpu"
    )
    assert ds.num_val_episodes == 1
    train_eps = {int(r) // 10 for r in ds.train_index.flatten()}
    val_eps = {int(r) // 10 for r in ds.val_index.flatten()}
    assert not train_eps & val_eps


def test_normalizer_uses_training_frames_only(tmp_path):
    path = tmp_path / "demo.zarr"
    write_zarr(path, _episodes(n_ep=5), {"task": "unit"})
    ds = DemoDataset(path, 4, 2, 1, val_ratio=0.2, device="cpu")
    train_rows = torch.unique(ds.train_index)
    val_rows = torch.unique(ds.val_index)
    before = {k: v.clone() for k, v in ds.normalizer_data().items()}
    for key in ds.data:
        ds.data[key][val_rows] += 10000
    after = ds.normalizer_data()
    for target, source in (
        ("action", "action"),
        ("agent_pos", "state"),
        ("point_cloud", "point_cloud"),
    ):
        torch.testing.assert_close(after[target], before[target])
        torch.testing.assert_close(after[target], ds.data[source][train_rows])


@pytest.mark.parametrize("field", ["action", "state", "point_cloud"])
@pytest.mark.parametrize("value", [np.nan, np.inf])
def test_dataset_rejects_nonfinite_values(tmp_path, field, value):
    episodes = _episodes()
    episodes[0][field].flat[1] = value
    path = tmp_path / "demo.zarr"
    write_zarr(path, episodes, {"task": "unit"})
    with pytest.raises(ValueError, match="finite"):
        DemoDataset(path, 4, 2, 1, device="cpu")


@pytest.mark.parametrize(
    ("field", "shape"),
    [
        ("action", (10, 30)),
        ("state", (10, 16)),
        ("point_cloud", (10, 16, 4)),
        ("state", (9, 17)),
        ("point_cloud", (10, 0, 3)),
    ],
)
def test_dataset_rejects_invalid_shapes(tmp_path, field, shape):
    episodes = _episodes(n_ep=1)
    path = tmp_path / "demo.zarr"
    write_zarr(path, episodes, {"task": "unit"})
    root = zarr.open_group(str(path), mode="a")
    root["data"].create_dataset(
        field,
        data=np.zeros(shape, dtype=np.float32),
        overwrite=True,
        chunks=tuple(max(1, n) for n in shape),
    )
    with pytest.raises(ValueError, match="shape|frames"):
        DemoDataset(path, 4, 2, 1, device="cpu")


@pytest.mark.parametrize(("column", "value"), [(0, 0.25), (0, 2), (27, 0), (30, -2)])
def test_dataset_rejects_invalid_trajectory_semantics(tmp_path, column, value):
    episodes = _episodes()
    episodes[0]["action"][0, column] = value
    path = tmp_path / "demo.zarr"
    write_zarr(path, episodes, {"task": "unit"})
    with pytest.raises(ValueError, match="flag|unit direction"):
        DemoDataset(path, 4, 2, 1, device="cpu")


@pytest.mark.parametrize("ends", [[0, 30], [10, 10, 30], [10, 31], [10.5, 30]])
def test_dataset_rejects_invalid_episode_boundaries(tmp_path, ends):
    path = tmp_path / "demo.zarr"
    write_zarr(path, _episodes(), {"task": "unit"})
    root = zarr.open_group(str(path), mode="a")
    root["meta"].create_dataset("episode_ends", data=np.asarray(ends), overwrite=True)
    with pytest.raises(ValueError, match="episode_ends"):
        DemoDataset(path, 4, 2, 1, device="cpu")


def test_dataset_rejects_no_training_windows(tmp_path):
    path = tmp_path / "demo.zarr"
    write_zarr(path, _episodes(n_ep=1, t=2), {"task": "unit"})
    with pytest.raises(ValueError, match="training windows"):
        DemoDataset(path, 4, 2, 1, device="cpu")


@pytest.mark.parametrize(
    "overrides",
    [
        {"n_obs_steps": 5},
        {"n_obs_steps": 0},
        {"n_action_steps": 0},
        {"n_action_steps": 4},
        {"horizon": 3},
        {"horizon": 0},
    ],
)
def test_model_rejects_invalid_temporal_configuration(overrides):
    cfg = PlannerModelCfg(down_dims=(32, 64, 128), **overrides)
    meta = {
        "obs": {"point_cloud": {"shape": [16, 3]}, "agent_pos": {"shape": [17]}},
        "action": {"shape": [31]},
    }
    with pytest.raises(ValueError, match="horizon|steps"):
        build_policy(cfg, meta)


def test_encoder_width_override_can_train_and_predict(tmp_path):
    path = tmp_path / "demo.zarr"
    write_zarr(path, _episodes(), {"task": "unit"})
    ds = DemoDataset(path, 4, 2, 1, device="cpu")
    cfg = PlannerModelCfg(
        down_dims=(32, 64, 128), encoder_output_dim=128, num_inference_steps=2
    )
    policy = build_policy(cfg, ds.shape_meta)
    norm = LinearNormalizer()
    norm.fit(ds.normalizer_data())
    policy.set_normalizer(norm)
    batch = ds.batch(ds.train_index[:2])
    loss, _ = policy.compute_loss(batch)
    assert torch.isfinite(loss)
    loss.backward()
    assert policy.predict_action(batch["obs"])["action"].shape == (2, 1, 31)


def test_checkpoint_round_trip(tmp_path):
    cfg = PlannerModelCfg(down_dims=(32, 64, 128), num_inference_steps=2)
    meta = {
        "obs": {"point_cloud": {"shape": [16, 3]}, "agent_pos": {"shape": [17]}},
        "action": {"shape": [31]},
    }
    policy = build_policy(cfg, meta)
    norm = LinearNormalizer()
    norm.fit(
        {
            "action": torch.from_numpy(_episodes(n_ep=1, t=50)[0]["action"]),
            "agent_pos": torch.randn(50, 17),
            "point_cloud": torch.randn(50, 16, 3),
        },
        last_n_dims=1,
    )
    policy.set_normalizer(norm)
    save_checkpoint(tmp_path / "ckpt", policy, cfg, meta, {"unit": True})
    loaded, info = load_checkpoint(tmp_path / "ckpt", device="cpu")
    assert info["info"] == {"unit": True}
    for k, v in policy.state_dict().items():
        torch.testing.assert_close(loaded.state_dict()[k], v)
    obs = {"point_cloud": torch.randn(2, 2, 16, 3), "agent_pos": torch.randn(2, 2, 17)}
    assert loaded.predict_action(obs)["action"].shape == (2, 1, 31)
