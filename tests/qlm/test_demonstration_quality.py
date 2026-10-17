import numpy as np
import pytest
from qlm_bench.backends.mujoco.quality import contact_evidence, projected_to_body


def test_missing_contact_is_unknown_not_failure():
    report = contact_evidence([{}, {"contact": {"valid": False, "fl_object": False, "body_object": False}}])
    assert report["status"] == "unknown" and report["unknown_boundaries"] == 2
    assert report["automatic_rejection"] is False


def test_measured_incidental_body_contact_is_not_a_rejection_predicate():
    report = contact_evidence([{"contact": {"valid": True, "status": "measured", "fl_object": True, "body_object": True}}, {}])
    assert report["status"] == "partial" and report["body_contact_boundaries"] == 1
    assert report["automatic_rejection"] is False


def test_endpoint_frame_inversion_and_input_ownership():
    points = np.array([[.3, .12, .15]])
    before = points.copy()
    actual = projected_to_body(points, [[0, 0, -1]], [.3])
    np.testing.assert_allclose(actual, [[.3, .12, -.15]])
    np.testing.assert_array_equal(points, before)
    # Rolled body: projected gravity=(0,-sin(a),-cos(a)).
    a = .3; c, s = np.cos(a), np.sin(a)
    rotation = np.array([[1, 0, 0], [0, c, s], [0, -s, c]])
    body = np.array([.3, .12, -.15])
    projected = rotation.T @ body + [0, 0, .3]
    np.testing.assert_allclose(projected_to_body([projected], [[0, -s, -c]], [.3]), [body])


def test_invalid_gravity_cannot_manufacture_posture_evidence():
    with pytest.raises(ValueError, match="unit"):
        projected_to_body([[.3, .12, .15]], [[0, 0, 0]], [.3])


def test_pending_reference_cannot_be_exported_as_formal_pilot(monkeypatch, tmp_path):
    from qlm_bench.backends.mujoco import replay_recording
    monkeypatch.setattr(replay_recording, 'verify_trace', lambda _: (
        {'demonstration_eligibility': 'review_required'}, None, None, None, None))
    output = tmp_path / 'must-not-exist'
    with pytest.raises(ValueError, match='quality review is pending'):
        replay_recording.record_trace('trace', 'model', output, episode_uid='test',
                                     ffmpeg='unused', ffprobe='unused', formal=True)
    assert not output.exists()
