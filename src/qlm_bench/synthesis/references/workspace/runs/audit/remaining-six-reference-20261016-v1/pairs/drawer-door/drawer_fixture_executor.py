"""a05 high-level path retargeted in the actual rigid cabinet frame.

Original successful a05 source is imported unchanged. Only absolute native9
endpoint/base-goal construction is rotated; robot reset stays fixed in the scene.
"""
from pathlib import Path
import importlib.util,numpy as np
from shared_executor import blend

spec=importlib.util.spec_from_file_location('preserved_drawer_a05',Path(__file__).parent/'sources/executors-v6.py')
preserved=importlib.util.module_from_spec(spec);spec.loader.exec_module(preserved)

class DrawerFixtureExecutor(preserved.DrawerExecutor):
 def configure(self):
  super().configure()
  self.config['recipe_id']='drawer-a05-rigid-fixture-frame-retarget-v6'
  body=self.model.body('primary').id
  self.fixture_rotation=self.runtime.physics.data[0].xmat[body].reshape(3,3).copy()
  self.base0=self.bar0[:2]-(self.fixture_rotation@np.array([.43,.14,0.]))[:2]
  self.base_goal=self.base0.copy()
 def offset(self,xyz):return self.bar0+self.fixture_rotation@np.asarray(xyz)
 def interaction(self,age,t,dt):
  below=self.offset([.078,0.,-.080]);inserted=self.offset([.078,0.,.015])
  if age<2.:return preserved.interp(self.interaction_world_start,below,age,2.)
  if age<4.:return preserved.interp(below,inserted,age-2.,2.)
  if self.pull_start is None:
   actual=self.fixture_rotation.T@(self.actual_world_point()-self.bar0)
   good=actual[2]>=-.005 and actual[0]>=.045 and abs(actual[1])<.035
   self.hook_ready_ticks=self.hook_ready_ticks+1 if good else 0
   self.segment='insert_and_confirm_actual_pose'
   if self.hook_ready_ticks>=3:self.pull_start=age
   return inserted
  self.segment='pull';pull_age=age-self.pull_start
  if pull_age<1.:return preserved.interp(inserted,self.offset([.030,0.,.015]),pull_age,1.)
  u=blend((pull_age-1.)/16.)
  self.base_goal=self.base0-(self.fixture_rotation@np.array([.245*u+.050*blend(pull_age/2.),0.,0.]))[:2]
  return self.offset([.030-.245*u,0.,.015])
