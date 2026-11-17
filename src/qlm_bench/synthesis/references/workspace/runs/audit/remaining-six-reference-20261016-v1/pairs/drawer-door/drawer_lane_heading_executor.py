"""Heading-held real U-hook path with a shorter reach and an interior lane.

The 20mm lane stays inside the unchanged168mm handle aperture. This is a
high-level reference candidate, not a changed task predicate or asset profile.
"""
from pathlib import Path
import importlib.util,numpy as np

spec=importlib.util.spec_from_file_location('preserved_heading_v3',Path(__file__).parent/'drawer_heading_executor.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)

class DrawerLaneHeadingExecutor(old.DrawerHeadingExecutor):
 def configure(self):
  super().configure();self.config['recipe_id']='drawer-heading-shorter-reach-interior-hook-lane-v8'
  self.base0+=(self.fixture_rotation@np.array([.030,0.,0.]))[:2];self.base_goal=self.base0.copy()
 def offset(self,xyz):
  point=np.asarray(xyz,dtype=float).copy();point[1]-=.020
  return self.bar0+self.fixture_rotation@point
