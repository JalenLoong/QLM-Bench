"""Retarget a07 heading to the actual cabinet orientation, fixed robot reset.

For nominal cabinet yaw0 this changes no numeric command/state versus a07.
For randomized fixture yaw the robot turns actively through native9 Omega.
"""
from pathlib import Path
import importlib.util,math

spec=importlib.util.spec_from_file_location('preserved_drawer_a07',Path(__file__).parent/'drawer_lane_heading_executor.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)

class DrawerFixtureHeadingExecutor(old.DrawerLaneHeadingExecutor):
 def configure(self):
  super().configure()
  self.config['recipe_id']='drawer-a07-rigid-fixture-frame-including-heading-v9'
  self.heading_target=math.atan2(float(self.fixture_rotation[1,0]),float(self.fixture_rotation[0,0]))
