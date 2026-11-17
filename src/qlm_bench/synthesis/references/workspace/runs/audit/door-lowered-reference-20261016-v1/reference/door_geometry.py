"""Read-only28cm Door geometry; same helpers used by offline and real expert."""
import math
import mujoco,numpy as np

def rotation_z(angle):
 c,s=math.cos(angle),math.sin(angle)
 return np.array([[c,-s,0.],[s,c,0.],[0.,0.,1.]])

def rotation_x(angle):
 c,s=math.cos(angle),math.sin(angle)
 return np.array([[1.,0.,0.],[0.,c,-s],[0.,s,c]])

class DoorGeometry:
 def __init__(self,model,profile,station_fraction=.5652173913043478):
  self.model=model;self.profile=profile
  self.lever_joint=model.joint(profile['lever_joint']).id
  self.bolt_joint=model.joint(profile['bolt_joint']).id
  self.hinge_joint=model.joint(profile['primary_joint']).id
  self.prefix=profile['lever_joint'].removesuffix('_lever_joint')
  self.primary=model.body('primary').id;self.frame=model.body(self.prefix+'_frame').id
  self.lever=int(model.jnt_bodyid[self.lever_joint]);self.bolt=int(model.jnt_bodyid[self.bolt_joint])
  self.foot=model.geom('FL').id;self.foot_body=int(model.geom_bodyid[self.foot])
  self.handle=model.geom(self.prefix+'_handle').id
  self.foot_radius=float(model.geom_size[self.foot,0]);self.bar_radius=float(model.geom_size[self.handle,0]);self.bar_half=float(model.geom_size[self.handle,1])
  q=np.empty(9);mujoco.mju_quat2Mat(q,model.geom_quat[self.handle]);self.handle_axis_local=q.reshape(3,3)[:,2]
  self.handle_point_local=model.geom_pos[self.handle]+self.handle_axis_local*((2*station_fraction-1)*self.bar_half)
  self.pivot_local=model.body_pos[self.lever].copy()
  self.lever_min=float(model.jnt_range[self.lever_joint,0]);self.lever_max=float(model.jnt_range[self.lever_joint,1])
  for index,axis in [(self.hinge_joint,[0,0,1]),(self.lever_joint,[1,0,0]),(self.bolt_joint,[0,1,0])]:np.testing.assert_allclose(model.jnt_axis[index],axis,atol=1e-12)
  np.testing.assert_allclose(model.body_quat[self.lever],[1,0,0,0],atol=1e-12)
  assert model.geom_type[self.handle]==mujoco.mjtGeom.mjGEOM_CAPSULE
  self.robot={model.body('base').id}
  for body in range(model.nbody):
   if int(model.body_parentid[body]) in self.robot:self.robot.add(body)
  self.asset_geoms={g for g in range(model.ngeom) if (model.geom(g).name or '').startswith(self.prefix+'_')}

 def joints(self,data):
  return tuple(float(data.qpos[int(self.model.jnt_qposadr[j])]) for j in [self.hinge_joint,self.lever_joint,self.bolt_joint])

 def fixture(self,data):
  return data.xpos[self.primary].copy(),data.xmat[self.frame].reshape(3,3).copy()

 def point(self,data,lever_angle=None,door_angle=None):
  door,lever,bolt=self.joints(data)
  if lever_angle is None:lever_angle=lever
  if door_angle is None:door_angle=door
  origin,fixture=self.fixture(data)
  return origin+fixture@rotation_z(door_angle)@(self.pivot_local+rotation_x(lever_angle)@self.handle_point_local)

 def leaf_rotation(self,data,door_angle=None):
  if door_angle is None:door_angle=self.joints(data)[0]
  return self.fixture(data)[1]@rotation_z(door_angle)

 def sphere(self,data):
  foot=data.geom_xpos[self.foot].copy();axis=data.geom_xmat[self.handle].reshape(3,3)[:,2];centre=data.geom_xpos[self.handle]
  top=max(float((centre-self.bar_half*axis)[2]),float((centre+self.bar_half*axis)[2]))+self.bar_radius
  jac=np.zeros((3,self.model.nv));rot=np.zeros_like(jac);mujoco.mj_jacGeom(self.model,data,jac,rot,self.foot)
  return dict(centre=foot,velocity=jac@data.qvel,bar_top=top,clearance=float(foot[2]-self.foot_radius-top),body_origin=data.xpos[self.foot_body].copy(),geom_offset_world=(foot-data.xpos[self.foot_body]).copy())

 def contacts(self,data):
  pairs=[];toe=[];handle_force=np.zeros(3);normal=0.;panel_normal=0.;nonFL=[]
  for index,contact in enumerate(data.contact[:data.ncon]):
   g1,g2=map(int,contact.geom)
   if g1 in self.asset_geoms and int(self.model.geom_bodyid[g2]) in self.robot:asset,robot=g1,g2
   elif g2 in self.asset_geoms and int(self.model.geom_bodyid[g1]) in self.robot:asset,robot=g2,g1
   else:continue
   wrench=np.zeros(6);mujoco.mj_contactForce(self.model,data,index,wrench);fn=max(0.,float(wrench[0]));frame=contact.frame.reshape(3,3);force_on_asset=frame.T@wrench[:3]*(1. if g2==asset else -1.)
   body=self.model.body(int(self.model.geom_bodyid[robot])).name or '';name=self.model.geom(asset).name or ''
   record=dict(robot_body=body,robot_geom=self.model.geom(robot).name,asset_geom=name,distance_m=float(contact.dist),normal_N=fn,actual_world_force_on_asset_N=force_on_asset.tolist());pairs.append(record)
   if asset==self.handle and body.startswith('FL_'):
    handle_force+=force_on_asset;normal+=fn
    if robot==self.foot:
     direction=frame[0]*(1. if g1==asset else -1.);toe.append(dict(normal_N=fn,handle_to_toe_normal=direction.tolist(),force_on_handle=force_on_asset.tolist()))
   if ('panel' in name or 'inset_front' in name) and body.startswith('FL_'):panel_normal+=fn
   if fn>2. and not body.startswith('FL_'):nonFL.append(record)
  upper=any(c['normal_N']>1. and c['handle_to_toe_normal'][2]>=.65 and c['force_on_handle'][2]<-.5 for c in toe)
  side=any(c['normal_N']>2. and c['handle_to_toe_normal'][2]<.35 for c in toe)
  return dict(pairs=pairs,actual_toe_handle=toe,actual_FL_handle_normal_N=normal,actual_FL_handle_world_force_N=handle_force.tolist(),true_upper_toe_contact=upper,side_toe_contact=side,actual_FL_panel_normal_N=panel_normal,other_robot_force_contacts=nonFL,read_only_actual_native_contacts=True,source='actual current Native MuJoCo contact wrench; not snapshot reconstructed force')
