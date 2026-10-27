import math

import pytest
import torch

from leg_manip.traj import (
    TrajParams,
    inverse_yaw_transform,
    param_dim,
    quat_to_yaw,
    rational_bezier,
    slerp_unit,
)


def _de_casteljau(ctrl: torch.Tensor, t: float) -> torch.Tensor:
    pts = ctrl.clone()
    while pts.shape[0] > 1:
        pts = (1 - t) * pts[:-1] + t * pts[1:]
    return pts[0]


def _random_params(batch: int, k: int = 6, seed: int = 0) -> TrajParams:
    g = torch.Generator().manual_seed(seed)
    dirs = torch.nn.functional.normalize(torch.randn(batch, 2, 3, generator=g), dim=-1)
    return TrajParams(
        flag=torch.randint(0, 2, (batch,), generator=g).float(),
        ctrl=torch.randn(batch, k, 3, generator=g),
        log_w=torch.rand(batch, k, generator=g) * math.log(2000.0),
        dir0=dirs[:, 0],
        dir1=dirs[:, 1],
    )


def test_bezier_endpoints_interpolate_first_and_last_point():
    p = _random_params(8)
    torch.testing.assert_close(p.position(torch.zeros(8)), p.ctrl[:, 0])
    torch.testing.assert_close(p.position(torch.ones(8)), p.ctrl[:, -1])


@pytest.mark.parametrize("t", [0.1, 0.37, 0.5, 0.9])
def test_equal_weights_reduce_to_plain_bezier(t):
    ctrl = torch.randn(6, 3)
    got = rational_bezier(ctrl, torch.full((6,), 7.0), torch.tensor(t))
    torch.testing.assert_close(got, _de_casteljau(ctrl, t))


def test_large_weight_pulls_curve_toward_control_point():
    ctrl = torch.zeros(3, 3)
    ctrl[1] = torch.tensor([0.0, 1.0, 0.0])
    ctrl[2] = torch.tensor([1.0, 0.0, 0.0])
    t = torch.tensor(0.5)
    low = rational_bezier(ctrl, torch.tensor([1.0, 1.0, 1.0]), t)
    high = rational_bezier(ctrl, torch.tensor([1.0, 1000.0, 1.0]), t)
    assert (high - ctrl[1]).norm() < 0.01 < (low - ctrl[1]).norm()


def test_slerp_endpoints_unit_norm_and_constant_speed():
    v0 = torch.tensor([1.0, 0.0, 0.0])
    v1 = torch.tensor([0.0, 1.0, 0.0])
    ts = torch.linspace(0, 1, 11)
    out = slerp_unit(v0.expand(11, 3), v1.expand(11, 3), ts)
    torch.testing.assert_close(out.norm(dim=-1), torch.ones(11))
    torch.testing.assert_close(out[0], v0)
    torch.testing.assert_close(out[-1], v1)
    angles = torch.acos((out * v0).sum(-1).clamp(-1, 1))
    torch.testing.assert_close(angles, ts * math.pi / 2, atol=1e-5, rtol=0)


def test_slerp_handles_parallel_and_opposite_vectors():
    v = torch.tensor([[0.0, 0.0, -1.0], [0.0, 0.0, -1.0]])
    w = torch.tensor([[0.0, 0.0, -1.0], [0.0, 0.0, 1.0]])
    out = slerp_unit(v, w, torch.tensor([0.5, 0.5]))
    assert torch.isfinite(out).all()
    torch.testing.assert_close(out.norm(dim=-1), torch.ones(2))
    torch.testing.assert_close(out[0], v[0])


@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
def test_slerp_near_antipodal_preserves_shortest_arc(dtype):
    v0 = torch.nn.functional.normalize(
        torch.tensor([1.0, 0.0, 1.0], dtype=dtype), dim=0
    )
    v1 = torch.nn.functional.normalize(
        -v0 + torch.tensor([0.0, -0.001, 0.0], dtype=dtype), dim=0
    )
    phases = torch.linspace(0, 1, 9, dtype=dtype)
    out = slerp_unit(v0, v1, phases)
    # The short arc is in the -Y half-plane, even though the vectors almost oppose.
    theta = math.pi - math.atan(0.001)
    tangent = torch.tensor([0.0, -1.0, 0.0], dtype=dtype)
    expected = torch.cos(phases[:, None] * theta) * v0
    expected += torch.sin(phases[:, None] * theta) * tangent
    torch.testing.assert_close(out, expected, atol=2e-6, rtol=2e-6)
    torch.testing.assert_close(out.norm(dim=-1), torch.ones_like(phases))


@pytest.mark.parametrize("antipodal", [False, True])
def test_slerp_preserves_original_endpoints_near_and_at_antipodes(antipodal):
    v0 = torch.tensor([1.0, 0.0, 0.0])
    v1 = torch.nn.functional.normalize(
        torch.tensor([-1.0, 0.0, 0.0 if antipodal else -0.001]), dim=0
    )
    out = slerp_unit(v0, v1, torch.tensor([0.0, 1.0]))
    torch.testing.assert_close(out, torch.stack([v0, v1]), rtol=0, atol=0)


def test_slerp_mixed_degenerate_batch_stays_unit_and_finite():
    v0 = torch.tensor([[1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    v1 = torch.tensor([[1.0, 0.0, 0.0], [-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    out = slerp_unit(v0, v1, torch.full((3,), 0.5))
    assert torch.isfinite(out).all()
    torch.testing.assert_close(out.norm(dim=-1), torch.ones(3))
    torch.testing.assert_close(out[0], v0[0])
    torch.testing.assert_close(out[1] @ v0[1], torch.tensor(0.0), atol=1e-6, rtol=0)
    torch.testing.assert_close(out[2], torch.tensor([2**-0.5, 2**-0.5, 0.0]))


def test_vector_round_trip():
    p = _random_params(5)
    vec = p.to_vector()
    assert vec.shape == (5, param_dim())
    q = TrajParams.from_vector(vec)
    for a, b in zip(
        (p.flag, p.ctrl, p.log_w, p.dir0, p.dir1),
        (q.flag, q.ctrl, q.log_w, q.dir0, q.dir1),
        strict=True,
    ):
        torch.testing.assert_close(a, b)


def test_frame_change_commutes_with_evaluation():
    p = _random_params(4)
    yaw = torch.tensor([0.3, -1.2, 2.5, 0.0])
    origin = torch.randn(4, 3)
    t = torch.rand(4)
    world = p.to_parent(yaw, origin)
    expected = inverse_yaw_transform(world.position(t), yaw, origin)
    torch.testing.assert_close(p.position(t), expected, atol=1e-5, rtol=1e-5)
    back = world.to_local(yaw, origin)
    torch.testing.assert_close(back.ctrl, p.ctrl, atol=1e-5, rtol=1e-5)
    torch.testing.assert_close(back.dir1, p.dir1, atol=1e-6, rtol=1e-6)


def test_quat_to_yaw():
    yaw = torch.tensor([0.0, 0.7, -2.0])
    quat = torch.stack(
        [torch.cos(yaw / 2), torch.zeros(3), torch.zeros(3), torch.sin(yaw / 2)], -1
    )
    torch.testing.assert_close(quat_to_yaw(quat), yaw)
