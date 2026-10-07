"""Reset must expose the new physical twist at the existing physics timestamp."""
from types import SimpleNamespace

import pytest

torch = pytest.importorskip("torch")
from rambo.utils.articulation import invalidate_reset_root_link_velocity


class ResetData:
    """Lazy root-link cache with the pinned backend's COM-to-link semantics."""
    def __init__(self):
        self._sim_timestamp = 3.0
        self.com_twist = torch.tensor([[1., 2., 3., 0., 0., 2.],
                                       [4., 5., 6., 1., 0., 0.]])
        self.com_offset_world = torch.tensor([[0.2, 0., 0.], [0., 0.3, 0.]])
        self._root_link_vel_w = SimpleNamespace(timestamp=-1., data=None)
        self._root_link_state_w = SimpleNamespace(timestamp=3., data=torch.ones(2, 13))
        self._root_state_w = SimpleNamespace(timestamp=3., data=torch.ones(2, 13))

    @property
    def root_link_vel_w(self):
        cache = self._root_link_vel_w
        if cache.timestamp < self._sim_timestamp:
            value = self.com_twist.clone()
            value[:, :3] -= torch.linalg.cross(value[:, 3:], self.com_offset_world)
            cache.data = value
            cache.timestamp = self._sim_timestamp
        return cache.data


def test_partial_reset_refreshes_link_velocity_without_zeroing_other_instances_or_time():
    data = ResetData()
    old = data.root_link_vel_w.clone()
    # Reproduce a COM write at the same timestamp after warming the link cache.
    data.com_twist[0] = torch.tensor([0.5, -0.5, 0., 0., 0., 1.])
    assert torch.equal(data.root_link_vel_w, old)
    invalidate_reset_root_link_velocity(SimpleNamespace(data=data))
    refreshed = data.root_link_vel_w
    assert torch.allclose(refreshed[0], torch.tensor([0.5, -0.7, 0., 0., 0., 1.]))
    assert torch.equal(refreshed[1], old[1])
    assert data._sim_timestamp == 3.0
    assert data._root_link_state_w.timestamp == -1.
    assert data._root_state_w.timestamp == -1.


def test_stationary_reset_returns_physical_zero_after_nonzero_previous_episode():
    data = ResetData()
    assert torch.count_nonzero(data.root_link_vel_w)
    data.com_twist.zero_()
    invalidate_reset_root_link_velocity(SimpleNamespace(data=data))
    assert torch.count_nonzero(data.root_link_vel_w) == 0
    assert data._sim_timestamp == 3.0


def test_unknown_cache_layout_fails_before_mutating_available_buffers():
    buffer = SimpleNamespace(timestamp=5.)
    data = SimpleNamespace(_root_link_vel_w=buffer)
    with pytest.raises(RuntimeError, match="cache layout"):
        invalidate_reset_root_link_velocity(SimpleNamespace(data=data))
    assert buffer.timestamp == 5.
