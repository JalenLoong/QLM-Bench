"""Optional read-only real Native wrench summary; disabled without output path."""
from pathlib import Path
import json,atexit
import numpy as np,mujoco

class ActualWrenchSummary:
 def configure(self):
  super().configure();self.wrench_rows=[];self.wrench_bucket=None;self.wrench_enabled=bool(self.config.get('wrench_diagnostic_file'))
  if self.wrench_enabled:atexit.register(self.flush_wrench)
 def flush_wrench(self):
  if not self.wrench_bucket or not self.wrench_bucket['samples']:return
  samples=self.wrench_bucket['samples'];row={'second':self.wrench_bucket['second'],'samples_50Hz':len(samples),'actual_block_xyz':samples[-1]['block'],'actual_block_yaw_deg':samples[-1]['yaw'],'actual_foot_local_xyz':samples[-1]['local_foot'],'actual_block_yaw_rate_rad_s':samples[-1]['yaw_rate'],'actual_foot_world_z':samples[-1]['foot_z']}
  row['projected_target_minus_actual_foot_world_mean_m']=np.mean([r['tracking_error_world'] for r in samples],axis=0).tolist();row['projected_target_minus_actual_foot_block_mean_m']=np.mean([r['tracking_error_block'] for r in samples],axis=0).tolist();row['actual_foot_z_min_max_m']=[min(r['foot_z'] for r in samples),max(r['foot_z'] for r in samples)]
  for group in ['FL_to_block','floor_to_block','floor_to_FL']:
   row[group]={'contact_boundaries':sum(bool(s[group]['hits']) for s in samples),'pairs':{}}
   for s in samples:
    for name in s[group]['hits']:row[group]['pairs'][name]=row[group]['pairs'].get(name,0)+1
   weight=sum(r[group]['normal_weight_N'] for r in samples);row[group]['normal_force_weighted_contact_local_xyz_m']=(sum((r[group]['weighted_contact_local'] for r in samples),np.zeros(3))/weight).tolist() if weight>0 else None
   for name in ['normal_force_world','tangent_force_world','total_force_world','normal_torque_about_block_world','tangent_torque_about_block_world','contact_torque_world']:
    row[group][name+'_mean_including_noncontact']=np.mean([s[group][name] for s in samples],axis=0).tolist()
  self.wrench_rows.append(row);self.wrench_bucket=None;path=Path(self.config['wrench_diagnostic_file']).resolve();assert path.is_relative_to(Path(__file__).resolve().parent);path.write_text(json.dumps({'role':'Actual Native50Hz wrench samples summarized1Hz; not a500Hz impulse integral and not mandatory new demonstration telemetry','wrench_collection_does_not_change_commands':True,'floor_to_FL_moments_are_on_FL_not_on_block':True,'force_convention':'Actual force on block (or floor-on-FL for floor_to_FL), geom2 positive; contact frame rows normal/tangent','rows':self.wrench_rows},indent=2)+'\n')
 def command(self):
  values,diag=super().command()
  if not self.wrench_enabled:return values,diag
  m=self.runtime.physics.model;d=self.runtime.physics.data[0];block=m.geom('sw_block').id;body=m.body('primary').id;foot=m.geom('FL').id;center=d.geom_xpos[block];R=d.geom_xmat[block].reshape(3,3);sample={}
  for group in ['FL_to_block','floor_to_block','floor_to_FL']:sample[group]={'hits':[],'normal_weight_N':0.,'weighted_contact_local':np.zeros(3),'normal_force_world':np.zeros(3),'tangent_force_world':np.zeros(3),'total_force_world':np.zeros(3),'normal_torque_about_block_world':np.zeros(3),'tangent_torque_about_block_world':np.zeros(3),'contact_torque_world':np.zeros(3)}
  for i,c in enumerate(d.contact[:d.ncon]):
   gs=list(map(int,c.geom));bodies=[int(m.geom_bodyid[g]) for g in gs];names=[m.geom(g).name for g in gs];fl=[k for k,b in enumerate(bodies) if (m.body(b).name or '').startswith('FL_')];group=None;receiver=None
   if block in gs:
    k=gs.index(block);other=1-k
    if other in fl:group='FL_to_block';receiver=k
    elif names[other]=='floor':group='floor_to_block';receiver=k
   elif 'floor' in names and fl:group='floor_to_FL';receiver=fl[0]
   if group is None:continue
   wrench=np.zeros(6);mujoco.mj_contactForce(m,d,i,wrench);frame=c.frame.reshape(3,3);sign=1. if receiver==1 else -1.;n=sign*frame[0]*wrench[0];f=sign*(frame.T@wrench[:3]);t=f-n;moment=sign*(frame.T@wrench[3:]);g=sample[group];g['normal_weight_N']+=abs(float(wrench[0]));g['weighted_contact_local']+=abs(float(wrench[0]))*(R.T@(c.pos-center));g['hits'].append('|'.join(names));g['normal_force_world']+=n;g['tangent_force_world']+=t;g['total_force_world']+=f;g['normal_torque_about_block_world']+=np.cross(c.pos-center,n);g['tangent_torque_about_block_world']+=np.cross(c.pos-center,t);g['contact_torque_world']+=moment
  tracking=np.asarray(diag['world_target'])-d.geom_xpos[foot];sample['tracking_error_world']=tracking.copy();sample['tracking_error_block']=R.T@tracking;velocity=np.zeros(6);mujoco.mj_objectVelocity(m,d,mujoco.mjtObj.mjOBJ_BODY,body,velocity,0);sample.update(block=center.tolist(),yaw=float(np.degrees(np.arctan2(R[1,0],R[0,0]))),local_foot=(R.T@(d.geom_xpos[foot]-center)).tolist(),yaw_rate=float(velocity[2]),foot_z=float(d.geom_xpos[foot,2]));second=int(self.runtime.physics.ticks[0])//500
  if self.wrench_bucket is None or second!=self.wrench_bucket['second']:self.flush_wrench();self.wrench_bucket={'second':second,'samples':[]}
  self.wrench_bucket['samples'].append(sample)
  return values,diag
