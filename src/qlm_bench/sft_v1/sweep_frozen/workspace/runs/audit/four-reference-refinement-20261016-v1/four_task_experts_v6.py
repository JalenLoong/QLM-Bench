"""User-requested high-level revisions only; original RAMBO/controller/physics execution."""
from pathlib import Path
import importlib.util
import numpy as np
R=Path('/home/jalen/workspace/WAM-Policy');OLD=R/'runs/audit/remaining-six-reference-20261016-v1'
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
sweep=module('unchanged_sweep_v15',OLD/'pairs/sweep-valve/sweep_geometric_entry_executor_v15.py')
fridge=module('unchanged_fridge_v7',OLD/'pairs/fridge-oven/executors_v7.py')
valve=module('unchanged_valve_v7',OLD/'pairs/sweep-valve/valve_mount_heading_executor_v7.py')

class Sweep(sweep.SweepExecutor):
    def configure(self):
        self.coord_ready=False;super().configure();self.coord_ready=True
        self.coord_block_start=self.runtime.task.geometric_center(0)[:2].copy()
        self.coord_heading=float(np.arctan2(self.direction[0],-self.direction[1]));self.coord_lower_start=None;self.coord_anchor=np.array([self.config.get('coordinated_entry_base_x_m',.23),self.fixed_base_y])
        assert abs(np.dot([np.cos(self.coord_heading),np.sin(self.coord_heading)],self.direction))<1e-10
        self.update_reach_goal()
    def update_reach_goal(self):
        if not getattr(self,'coord_ready',False):return super().update_reach_goal()
        super().update_reach_goal();safe_cap=float(self.base_x_cap);safe_binding=self.reach_clearance_binding
        t=float(self.runtime.physics.ticks[0])*.002;stage=getattr(self,'entry_stage','raise')
        if stage in ['align','lower','sweep'] and self.coord_lower_start is None:self.coord_lower_start=t
        ratio=0. if self.coord_lower_start is None else np.clip((t-self.coord_lower_start)/2.,0,1)
        smooth=ratio*ratio*(3-2*ratio);x=self.coord_anchor[0]+(self.config.get('coordinated_push_base_x_m',.29)-self.coord_anchor[0])*smooth
        p=self.runtime.task.geometric_center(0)[:2];goal=np.array([np.mean(self.runtime.profile['goal_x']),np.mean(self.runtime.profile['goal_y'])])
        progress=np.clip(float(np.dot(p-self.coord_block_start,self.direction)),0,float(np.linalg.norm(goal-self.coord_block_start))) if stage=='sweep' else 0.
        x+=max(0.,float(p[0]-self.coord_block_start[0])) if stage=='sweep' else 0.
        self.base_goal=np.array([min(x,safe_cap),self.coord_anchor[1]])+self.direction*progress
        self.base_x_cap=safe_cap;self.reach_clearance_binding=safe_binding
    def command(self):
        values,diag=super().command();d=self.runtime.physics.data[0];m=self.runtime.physics.model;rotation=d.xmat[m.body('base').id].reshape(3,3)
        fl=d.geom_xpos[m.geom('FL').id];fr=d.geom_xpos[m.geom('FR').id]
        diag.update(body_goal_follows_actual_block_toward_goal=True,FL_minus_FR_body_lateral_m=float((fl-fr)@rotation[:,1]),coordinated_base_goal=self.base_goal.tolist())
        return values,diag

class Fridge(fridge.Fridge):
    pass # Recipe starts the larger raised/forward carry at2.0s.

class Valve(valve.ValveExecutor):
    def configure(self):super().configure();self.early_interaction_started=False
    def command(self):
        t=float(self.runtime.physics.ticks[0])*.002
        if not self.early_interaction_started and t>=self.config.get('early_interaction_s',6.):
            self.early_interaction_started=True;self.base_goal=self.core.robot.position[0,:2].cpu().numpy().astype(float)
            self.base_feedback=self.base_goal.copy();self.lateral_integral=0.
            self.transition('interaction',t);self.interaction_start=t;self.interaction_world_start=self.phase_world_start.copy()
        values,diag=super().command();diag['early_stop_and_manipulation_s']=6.;return values,diag
