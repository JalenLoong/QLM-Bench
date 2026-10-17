"""Evidence-only demonstration review, separate from task outcome/admission.

These metrics are not approved SFT thresholds. In particular, absent contact is
unknown and incidental body contact does not prove body-assisted manipulation.
No simulator, controller or renderer is loaded by this offline review.
"""
from pathlib import Path

import numpy as np

from .trace import verify_trace, sha


def projected_to_body(points, gravity, height):
    """Invert the retained analytical projected-COM endpoint representation."""
    points = np.asarray(points, dtype=np.float64)
    gravity = np.asarray(gravity, dtype=np.float64)
    height = np.asarray(height, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 3 or gravity.shape != points.shape or height.shape != points.shape[:1]:
        raise ValueError("Expected aligned endpoint/gravity/height arrays")
    if not all(np.isfinite(x).all() for x in (points, gravity, height)):
        raise ValueError("Nonfinite state cannot supply quality evidence")
    if not np.allclose(np.linalg.norm(gravity, axis=1), 1, atol=1e-3):
        raise ValueError("Expected actual unit projected gravity")
    col1 = np.stack((-gravity[:, 2], np.zeros(len(gravity)), gravity[:, 0]), axis=1)
    norm = np.linalg.norm(col1, axis=1, keepdims=True)
    if np.any(norm < 1e-8):
        raise ValueError("Degenerate roll/pitch reference")
    col1 /= norm
    col2 = np.cross(-gravity, col1)
    col2 /= np.linalg.norm(col2, axis=1, keepdims=True)
    rotation = np.stack((col1, col2, -gravity), axis=-1)
    relative = points.copy()
    relative[:, 2] -= height
    return np.einsum("nij,nj->ni", rotation, relative)


def contact_evidence(boundaries):
    result = {"known_boundaries": 0, "unknown_boundaries": 0,
              "fl_contact_boundaries": 0, "body_contact_boundaries": 0}
    for boundary in boundaries:
        row = boundary.get("contact", {})
        known = row.get("valid") is True and row.get("status") == "measured" and all(
            isinstance(row.get(key), (bool, np.bool_)) for key in ("fl_object", "body_object"))
        if not known:
            result["unknown_boundaries"] += 1
            continue
        result["known_boundaries"] += 1
        result["fl_contact_boundaries"] += int(row["fl_object"])
        result["body_contact_boundaries"] += int(row["body_object"])
    result["status"] = "unknown" if not result["known_boundaries"] else "partial" if result["unknown_boundaries"] else "measured"
    result["automatic_rejection"] = False
    return result


def analyze_trace(path):
    """Read an existing successful trace without relabeling its acceptance."""
    path = Path(path)
    manifest, arrays, telemetry, commands, terminal = verify_trace(path)
    boundaries = telemetry["boundaries"]
    states = [b["state"] for b in boundaries]
    n = len(commands)
    height = np.array([s["observation.state.base.position"][2] for s in states])
    gravity = np.array([s["observation.state.projected_gravity"] for s in states])
    foot = projected_to_body([s["observation.state.fl_ee_position"] for s in states], gravity, height)
    actions = np.array([c["executed"] for c in commands])
    target_body = projected_to_body(actions[:, 3:6], gravity[:-1], height[:-1])
    hip = np.rad2deg([s["observation.state.joint_position"][0] for s in states])
    phases = [c.get("extensions", {}).get("expert", {}).get("phase", "unknown") for c in commands]
    late = np.arange(n) >= n // 2
    pushing = np.array([p == "straight_push" for p in phases])
    base = np.array([s["observation.state.base.position"] for s in states])
    steps = np.linalg.norm(np.diff(actions[:, 3:6], axis=0), axis=1)
    crossings = (foot[:-1, 1] < 0) & pushing
    phase_edges = [i for i in range(1, n) if phases[i] != phases[i - 1]]
    world_targets=[c.get('extensions',{}).get('expert',{}).get('commanded_contact_point') for c in commands]
    world_steps=None
    if all(v is not None for v in world_targets):
        world_steps=np.linalg.norm(np.diff(np.asarray(world_targets),axis=0),axis=1)
    report = {
        "schema": "qlm-demonstration-quality-review-v1", "candidate_id": manifest["scene"]["candidate_id"],
        "trace_manifest_sha256": sha(path / "manifest.json"), "n_actions": n,
        "task_outcome": {key: terminal[key] for key in ("success", "fallen", "timed_out") if key in terminal},
        "task_predicate_changed": False, "contact": contact_evidence(boundaries),
        "measured_FL_body_y_min_m": float(foot[:, 1].min()),
        "measured_FL_body_y_terminal_m": float(foot[-1, 1]),
        "late_measured_FL_body_y_min_m": float(foot[:-1, 1][late].min()),
        "late_FL_hip_min_deg": float(hip[:-1][late].min()), "terminal_FL_hip_deg": float(hip[-1]),
        "push_body_midline_crossing_s": float(crossings.sum() * .02),
        "commanded_FL_body_y_min_m": float(target_body[:, 1].min()),
        "native_target_step_max_m": float(steps.max()) if len(steps) else 0.,
        "world_target_step_max_m": float(world_steps.max()) if world_steps is not None and len(world_steps) else None,
        "base_terminal_xy_m": base[-1, :2].tolist(),
        "phase_transitions": [{"command_index": i, "from": phases[i - 1], "to": phases[i],
                               "native_target_step_m": float(steps[i - 1])} for i in phase_edges],
        "eligibility": "review_required", "reused_in_new_pilot": False,
        "note": "Measurements are review evidence, not universal posture thresholds or task failure. No existing artifact is modified.",
    }
    curves = {"time_s": arrays["simulation_time_ns"] / 1e9, "measured_fl_body": foot,
              "commanded_fl_body": target_body, "FL_hip_deg": hip, "base_world": base}
    return report, curves
