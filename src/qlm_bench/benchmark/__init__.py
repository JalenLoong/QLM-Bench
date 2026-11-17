"""QLM-Bench Standard100: cases, protocol, runner and the live (RPC) evaluation entry point.

    python -m qlm_bench.benchmark fetch  --output <resource_root>
    python -m qlm_bench.benchmark run    --resource-root <resource_root> --policy-port <port> --policy-seed 42 --output <dir>
"""
from qlm_bench.benchmark.cases import EvalCase, EvaluationProtocol, TrialSpec, load_case
from qlm_bench.benchmark.results import summarize, validate_result, write_result
from qlm_bench.benchmark.runner import EvaluationRunner, StepResult, TerminalSnapshot

__all__ = ["EvalCase", "EvaluationProtocol", "TrialSpec", "EvaluationRunner", "StepResult", "TerminalSnapshot",
           "summarize", "validate_result", "write_result", "load_case", "run", "POLICY_SEEDS"]


def __getattr__(name):
    # The live runner imports the simulator stack; load it on first use only.
    if name in ("run", "POLICY_SEEDS"):
        from qlm_bench.benchmark import evaluate
        return getattr(evaluate, name)
    raise AttributeError(name)
