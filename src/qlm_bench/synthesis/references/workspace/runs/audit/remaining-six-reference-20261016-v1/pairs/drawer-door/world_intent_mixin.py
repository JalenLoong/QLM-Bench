"""Expert-only world motion limiting; preserve raw native9 intent for RAMBO.

No core/IK/PD/QP/history changes. The original core still computes its own IK,
residual and physical motor clamp. The shared expert projection is monitored but
is not substituted for the high-level world intent delivered to the actor.
"""
import numpy as np,torch
from qlm_bench.controllers.rambo.math import quat_apply,quat_apply_inverse,quat_mul,quat_inv

class WorldIntentMixin:
 def initialize_world_intent(self):
  self.intent_world_reference=None;self.intent_world_velocity=np.zeros(3);self.intent_time=None;self.expected_previous_native_ee=None
 def command(self):
  # These are the previous completed native9 interval's actual core inputs.
  seen=self.core._ee_pos_commands[0].detach().cpu().numpy().copy()
  history=self.core._obs_history[0,-1,-24:-21].detach().cpu().numpy().copy()
  expected=self.expected_previous_native_ee
  match=None if expected is None else bool(np.array_equal(seen,np.asarray(expected,dtype=np.float32)))
  if match is False:raise RuntimeError('Core did not retain the previously submitted native9 EE intent')
  values,diag=super().command();t=float(self.runtime.physics.data[0].time);dt=.02 if self.intent_time is None else t-self.intent_time;self.intent_time=t
  if not 0<dt<=.020001:raise ValueError('One raw-world intent command per50Hz boundary required')
  wanted=diag.get('unprojected_world_target');helper_world=diag.get('world_target')
  yaw_frame=quat_mul(self.core.base_quat,quat_inv(self.core.base_quat_rp));origin=self.core.robot.position[0].clone();origin[2]=0.
  if self.phase=='interaction' and wanted is not None:
   wanted=np.asarray(wanted,dtype=float)
   if self.intent_world_reference is None:self.intent_world_reference=np.asarray(helper_world,dtype=float).copy()
   delta=wanted-self.intent_world_reference;speed=float(self.config.get('world_intent_speed_m_s',.055));acc=float(self.config.get('world_intent_acceleration_m_s2',.12))
   velocity=delta/dt;norm=float(np.linalg.norm(velocity))
   if norm>speed:velocity*=speed/norm
   step=np.clip(velocity-self.intent_world_velocity,-acc*dt,acc*dt);self.intent_world_velocity+=step
   next_world=self.intent_world_reference+self.intent_world_velocity*dt
   crossing=(wanted-self.intent_world_reference)*(wanted-next_world)<=0
   next_world[crossing]=wanted[crossing];self.intent_world_velocity[crossing]=0.
   native=quat_apply_inverse(yaw_frame,torch.tensor(next_world[None],dtype=torch.float32,device=self.core.device)-origin[None])[0].cpu().tolist();values[3:6]=native
   diag['helper_projected_world_reference_not_sent']=helper_world
   if 'reference_geometric_joints_rad' in diag:diag['helper_projection_joints_not_core_target']=diag.pop('reference_geometric_joints_rad')
   diag['world_target']=next_world.tolist();diag['requested_world_intent']=wanted.tolist();diag['world_intent_velocity_m_s']=self.intent_world_velocity.tolist()
  else:self.intent_world_velocity[:]=0.
  # Store the actually emitted command in world coordinates at this boundary.
  sent=quat_apply(yaw_frame,torch.tensor([values[3:6]],dtype=torch.float32,device=self.core.device))+origin[None]
  self.intent_world_reference=sent[0].cpu().numpy().astype(float);self.expected_previous_native_ee=np.asarray(values[3:6],dtype=np.float32).copy()
  diag.update(actor_target_mode='raw native9 world intent; unchanged core original IK and motor clamp',core_seen_previous_native_ee=seen.tolist(),latest_history_previous_native_ee=history.tolist(),previous_native_ee_match=match,latest_history_matches_seen=bool(np.array_equal(history,seen)),actual_emitted_world_reference=self.intent_world_reference.tolist())
  return values,diag
