"""A09 guidance with optional stroke/shift continuation; task success is authoritative."""
from pathlib import Path
import importlib.util
R=Path('/home/jalen/workspace/WAM-Policy');P=R/'runs/audit/sweep-a09-scope-20261016-v1/retarget-v1/retarget_executor.py'
spec=importlib.util.spec_from_file_location('legacy_a09_geometry_guidance',P);legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
OPTIONAL_WAIT_ROUTES={'hold_unconfirmed_first_stroke_no_body_shift','reacquire_final_side_contact_body_held'}
class Sweep(legacy.Sweep):
 def command(self):
  values,diag=super().command();t=float(self.runtime.physics.ticks[0])*.002;reason=None
  if self.route in OPTIONAL_WAIT_ROUTES:
   reason=self.route;self.enter('final_sweep_body_held',t)
  elif self.route=='body_shift_right_foot_world_held' and t-self.shift_start>=self.config['body_shift_seconds']:
   reason='side_shift_reference_ramp_finished_without_stopped_gate';self.enter('final_sweep_body_held',t)
  # Keep actual commanded-stage diagnostics intact; next_route describes only
  # the following decision. Do not invent stable-contact/completed-body events.
  diag.update(sequence_admission_required=False,optional_wait_bypassed=reason,optional_next_route=self.route,A09_is_strategy_guidance=True)
  return values,diag
