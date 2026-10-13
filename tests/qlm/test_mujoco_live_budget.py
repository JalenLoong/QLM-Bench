"""Full-horizon execution cannot silently stop at the former8-chunk guard."""
import pytest
from qlm_bench.backends.mujoco.live import execution_budget


def test_full_horizon_budget_is_distinct_from_model_window():
    assert execution_budget(1,24)==75
    assert execution_budget(1,24,75)==75
    assert execution_budget(2,2.02)==7
    with pytest.raises(ValueError,match='too small'):
        execution_budget(1,24,8)


@pytest.mark.parametrize('seconds',[float('nan'),float('inf'),24.02,.32])
def test_horizon_guard_is_finite_and_bounded(seconds):
    with pytest.raises(ValueError):execution_budget(1,seconds)
