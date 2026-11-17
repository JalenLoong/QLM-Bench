"""Trial outcome tables: every expected trial must have an outcome before a success rate is reported."""
from __future__ import annotations

from copy import deepcopy
import json
import math
from pathlib import Path
import re
import shutil
import tempfile
from typing import Mapping

from qlm_bench.benchmark.cases import EvaluationProtocol, TrialSpec
from qlm_bench.contracts.policy.physical import ACTION_SCHEMA, COMMAND_INTERVAL_NS, identity, timestamp

RESULT_SCHEMA = "qlm-evaluation-result-v1"
OUTCOMES = ("success", "failure", "timeout", "error", "not_run")


def _protocol(record):
    try:
        values = deepcopy(dict(record))
        values["expected_trials"] = tuple(TrialSpec(**item) for item in values["expected_trials"])
        return EvaluationProtocol(**values)
    except (KeyError, TypeError) as error:
        raise ValueError("Incomplete or malformed evaluation protocol") from error


def validate_result(manifest: Mapping, outcomes) -> dict:
    """Check that every expected trial has a well-formed outcome row; failed trials are never dropped."""
    if not isinstance(manifest, Mapping) or manifest.get("schema") != RESULT_SCHEMA:
        raise ValueError("Unsupported evaluation result schema")
    identity(manifest.get("submission_id"), "submission_id")
    protocol = _protocol(manifest.get("protocol"))
    if manifest.get("expected_trials") != protocol.record()["expected_trials"]:
        raise ValueError("Manifest/protocol expected trial membership mismatch")
    if manifest.get("scope") != protocol.scope:
        raise ValueError("Manifest/protocol scope mismatch")
    expected = {item.trial_id: item for item in protocol.expected_trials}
    schedule = {"schema": ACTION_SCHEMA, "command_interval_ns": COMMAND_INTERVAL_NS,
                "mode": "synchronous_single_command", "desired_force": "zero"}
    actual_schedule = dict(manifest.get('action_scheduling', {}))
    mode = actual_schedule.get('mode')
    actual_schedule['mode'] = 'synchronous_single_command'
    if mode not in ('synchronous_single_command','synchronous_chunk16') or actual_schedule != schedule:
        raise ValueError("Result must record the fixed synchronous native9 force-zero scheduling")
    case_identities = manifest.get("cases", {})
    for trial in expected.values():
        if case_identities.get(trial.case_id, {}).get("task_id") != trial.task_id:
            raise ValueError("Result must describe the case of every expected trial")
    rows = list(outcomes)
    if not rows:
        raise ValueError("Complete trial table required")
    attempts = {}
    trials = {trial_id: [] for trial_id in expected}
    for row in rows:
        needed = {"trial_id", "attempt_id", "case_id", "task_id", "policy_seed", "outcome",
                  "termination_reason", "simulation_time_ns", "wall_time_s", "executed_commands",
                  "retry_of", "terminal_before_reset"}
        if not isinstance(row, Mapping) or not needed <= set(row):
            raise ValueError("Incomplete trial outcome")
        trial_id, attempt_id = row["trial_id"], row["attempt_id"]
        identity(attempt_id, "attempt ID")
        if trial_id not in expected or attempt_id in attempts:
            raise ValueError("Unexpected trial or duplicated attempt")
        trial = expected[trial_id]
        if type(row["policy_seed"]) is not int or (row["case_id"], row["task_id"], row["policy_seed"]) != \
                (trial.case_id, trial.task_id, trial.policy_seed):
            raise ValueError("Trial case/task/policy seed mismatch")
        if row["outcome"] not in OUTCOMES:
            raise ValueError("Unsupported outcome")
        identity(row["termination_reason"], "termination reason")
        timestamp(row["simulation_time_ns"])
        wall = row["wall_time_s"]
        if isinstance(wall, bool) or not isinstance(wall, (int, float)) or not math.isfinite(wall) or wall < 0:
            raise ValueError("Finite nonnegative wall duration required")
        count = row["executed_commands"]
        if type(count) is not int or count < 0 or type(row["terminal_before_reset"]) is not bool:
            raise ValueError("Invalid execution/terminal evidence")
        if row["outcome"] in ("success", "failure", "timeout") and not row["terminal_before_reset"]:
            raise ValueError("Task outcomes require pre-reset terminal evidence")
        if row["terminal_before_reset"]:
            evidence = row.get("terminal_evidence")
            if not isinstance(evidence, Mapping) or not isinstance(evidence.get("evaluator_state"), Mapping) or \
                    not evidence["evaluator_state"] or not isinstance(evidence.get("rgb"), Mapping) or \
                    not set(case_identities[trial.case_id]["camera_keys"]) <= set(evidence["rgb"]):
                raise ValueError("Task outcomes require terminal task state and declared policy RGB hashes")
            for frame in evidence["rgb"].values():
                if not isinstance(frame, Mapping) or frame.get("dtype") != "uint8" or \
                        not re.fullmatch(r"[0-9a-f]{64}", str(frame.get("sha256", ""))) or \
                        not isinstance(frame.get("shape"), (list, tuple)) or len(frame["shape"]) != 3 or \
                        frame["shape"][-1] != 3 or any(type(n) is not int or n < 1 for n in frame["shape"]):
                    raise ValueError("Invalid terminal RGB identity")
        if row["outcome"] == "not_run" and (count or row["simulation_time_ns"] or wall):
            raise ValueError("Not-run outcome cannot contain execution evidence")
        retry = row["retry_of"]
        prior = trials[trial_id]
        if not prior:
            if retry is not None:
                raise ValueError("First attempt cannot be a retry")
        elif retry != prior[-1]["attempt_id"] or attempts[retry]["trial_id"] != trial_id:
            raise ValueError("Retries must form an explicit same-trial attempt chain")
        if prior and protocol.error_policy == 'exclude_and_retry' and any(r['outcome'] in ('success','failure','timeout') for r in prior):
            raise ValueError('A valid task outcome cannot be retried or selected for success')
        attempts[attempt_id] = row
        prior.append(row)
    missing = [key for key, records in trials.items() if not records]
    if missing:
        raise ValueError("Missing expected trials: " + ", ".join(missing))
    metrics = _summarize(protocol, trials)
    return {"schema": RESULT_SCHEMA, "passed": True, "complete_trial_table": True,
            "expected_trials": len(expected), "attempts": len(rows), "metrics": metrics,
            "complete": metrics["status"] == "scored"}


def _summarize(protocol, trials):
    chosen = [(next((r for r in records if r['outcome'] in ('success','failure','timeout')), records[-1])
               if protocol.retry_selection == 'first_non_error_attempt' else
               records[0 if protocol.retry_selection == 'first_attempt' else -1]) for records in trials.values()]
    by_task = {}
    unfinished = False
    invalid_error = False
    for row in chosen:
        counts = by_task.setdefault(row["task_id"], {key: 0 for key in OUTCOMES})
        counts[row["outcome"]] += 1
        unfinished |= row["outcome"] == "not_run" or (protocol.error_policy == "exclude_and_retry" and row["outcome"] == "error")
        invalid_error |= row["outcome"] == "error" and protocol.error_policy == "invalidate"
    if protocol.scope == "engineering_diagnostic":
        status = "engineering_diagnostic"
    elif unfinished:
        status = "incomplete"
    elif invalid_error:
        status = "invalid_error"
    else:
        status = "scored"
    for task, counts in by_task.items():
        expected_count = sum(1 for trial in protocol.expected_trials if trial.task_id == task)
        counts["expected_trials"] = expected_count
        counts["success_rate"] = counts["success"] / expected_count if status == "scored" else None
    aggregate = None
    if status == "scored":
        successes = sum(counts["success"] for counts in by_task.values())
        aggregate = {"success": successes, "trials": len(chosen), "success_rate": successes / len(chosen)}
    return {"status": status, "per_task": by_task, "error_policy": protocol.error_policy,
            "retry_selection": protocol.retry_selection, "aggregate": aggregate}


def summarize(manifest, outcomes):
    return validate_result(manifest, outcomes)["metrics"]


def write_result(directory, manifest, outcomes):
    """Write a new local result directory; PyArrow is loaded only for artifact writing."""
    rows = list(outcomes)
    report = validate_result(manifest, rows)
    root = Path(directory)
    if root.exists():
        raise FileExistsError("Use a fresh result directory")
    import pyarrow as pa
    import pyarrow.parquet as pq
    manifest_json = json.dumps(manifest, indent=2, allow_nan=False) + "\n"
    summary_json = json.dumps(report["metrics"], indent=2, allow_nan=False) + "\n"
    table = pa.Table.from_pylist(rows)
    root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".evaluation-", dir=root.parent))
    try:
        (staging / "run_manifest.json").write_text(manifest_json)
        pq.write_table(table, staging / "episodes.parquet")
        (staging / "summary.json").write_text(summary_json)
        staging.rename(root)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return report
