"""Track acceptance statistics and warm starting from the lift stage."""

import math

import torch

from leg_manip.eval.gate import TRACK_LIMITS, summarize_gate


def _data(t=50, n=10):
    pos = torch.full((t, n), 0.05)
    z = torch.full_like(pos, 0.02)
    contact = torch.zeros_like(pos, dtype=torch.bool)
    raised = torch.ones_like(pos, dtype=torch.bool)
    fell = torch.zeros(n, dtype=torch.bool)
    return pos, z, contact, raised, fell


def test_track_gate_counts_contact_only_while_the_target_is_raised():
    pos, z, contact, raised, fell = _data()
    contact[:, :] = True
    raised[:, :] = False  # Ground-level targets: touching is allowed.
    r = summarize_gate(pos, z, contact, fell, TRACK_LIMITS, contact_mask=raised)
    assert r["passed"] and r["manip_ground_contact_fraction"] == 0
    raised[:10] = True  # 10 raised samples, all touching -> 100% for every env.
    r = summarize_gate(pos, z, contact, fell, TRACK_LIMITS, contact_mask=raised)
    assert not r["passed"] and r["manip_ground_contact_fraction"] == 1


def test_track_gate_applies_its_own_limits_and_exact_rate_boundaries():
    pos, z, contact, raised, fell = _data(n=20)
    pos[:, :4] = TRACK_LIMITS.position_m + 0.01  # 16/20 = 80% succeed.
    fell[4] = True  # 1/20 = 5% early terminations.
    r = summarize_gate(pos, z, contact, fell, TRACK_LIMITS, contact_mask=raised)
    assert r["successful_envs"] == 15 and not r["passed"]
    fell[4] = False
    r = summarize_gate(pos, z, contact, fell, TRACK_LIMITS, contact_mask=raised)
    assert r["successful_envs"] == 16 and r["passed"]


def test_track_gate_fails_on_nonfinite_errors():
    pos, z, contact, raised, fell = _data()
    z[3, 2] = math.nan
    r = summarize_gate(pos, z, contact, fell, TRACK_LIMITS, contact_mask=raised)
    assert not r["passed"] and r["nonfinite_envs"] == 1
