"""Original v8 contact/reach; only high-level contact height changes via recipe."""
from pathlib import Path
import importlib.util
p=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('retained_sweep_v8',p/'sweep_geometry_reach_executor_v8.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
spec=importlib.util.spec_from_file_location('optional_actual_wrench',p/'actual_wrench_summary_mixin.py');diag=importlib.util.module_from_spec(spec);spec.loader.exec_module(diag)
class SweepExecutor(diag.ActualWrenchSummary,old.SweepExecutor):
 pass
