"""Shared read-only geometric intent for preflight and original-native9 expert."""
import math,numpy as np
from door_geometry import rotation_z,rotation_x

class DoorPlan:
 def __init__(self,geometry,config):
  self.g=geometry;self.config=config;self.heading=math.radians(config.get('relative_heading_deg',-10.));self.base_offset=np.array(config.get('base_offset_fixture_xy_m',[-.52,-.52]));panel=geometry.model.geom(geometry.prefix+'_panel').id
  self.panel_x=float(geometry.model.geom_pos[panel,0]-geometry.model.geom_size[panel,0]-geometry.foot_radius)
  self.panel_y=float(config.get('panel_local_y_m',-.25));self.panel_z=float(geometry.pivot_local[2]-.04)

 def neutral_top(self,data,door_angle=None):
  g=self.g;origin,fixture=g.fixture(data);theta=g.joints(data)[0] if door_angle is None else door_angle;rot=fixture@rotation_z(theta);centre=origin+rot@(g.pivot_local+g.model.geom_pos[g.handle]);axis=rot@g.handle_axis_local
  return max(float((centre-g.bar_half*axis)[2]),float((centre+g.bar_half*axis)[2]))+g.bar_radius

 def neutral_base(self,data):
  origin,fixture=self.g.fixture(data)
  return origin[:2]+fixture[:2,:2]@self.base_offset

 def hover(self,data,ready=False):
  g=self.g;p=g.point(data,0.);rot=g.leaf_rotation(data)
  if ready:p+=rot@np.array([-.064,-.064*math.tan(self.heading),0.])
  p[2]=self.neutral_top(data)+g.foot_radius+.004
  return p

 def press(self,data,angle,depth=.002):
  p=self.g.point(data,angle);p[2]+=self.g.foot_radius+self.g.bar_radius-depth
  return p

 def press_base(self,data,angle):
  return self.neutral_base(data)+(self.g.point(data,angle)-self.g.point(data,0.))[:2]

 def panel(self,data,door_angle,depth=.004):
  origin,fixture=self.g.fixture(data)
  return origin+fixture@rotation_z(door_angle)@np.array([self.panel_x+depth,self.panel_y,self.panel_z])

 def panel_base(self,data,door_angle):
  point=self.panel(data,door_angle,0.);rot=self.g.leaf_rotation(data,door_angle)@rotation_z(self.heading)
  return point[:2]-(rot@np.array([.40,.15,0.]))[:2]
