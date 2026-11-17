"""Three MuJoCo engineering candidates with real contacts and retained predicates."""
from pathlib import Path
import hashlib
import itertools
import json
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
from qlm_bench.tasks.predicates import physical_condition
from qlm_bench.data.lerobot.task_state import push_progress
from qlm_bench.tasks.success import PolicySuccessHold,PressSuccessHold


INSTRUCTIONS={'push_box':'Push the box into the target area.','press_button':'Press the button.',
              'lift_basket':'Lift the basket.'}


class TaskState:
    def __init__(self,physics,profile):
        self.physics=physics;self.profile=profile;self.task=profile['task_id']
        m=physics.model
        self.body=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_BODY,'primary')
        self.hold=np.zeros(physics.count,dtype=int)
        self.through=np.zeros(physics.count,dtype=bool)
        self.initial_center_x=np.zeros(physics.count,dtype=float)
        self.success_holds=[PressSuccessHold(profile['threshold_m']) if self.task=='press_button'
                            else PolicySuccessHold(profile.get('success_hold_commands',3))
                            for _ in range(physics.count)]
        if self.task=='kick_ball_to_goal':
            from qlm_bench.backends.mujoco.kick_goal import GoalEntry
            self.goal_entries=[GoalEntry(profile['goal_geometry'],profile['ball_radius_m'])
                               for _ in range(physics.count)]
        self.reset()

    def reset(self,indices=None):
        """Capture each lane's real reset center after its physics reset."""
        indices=range(self.physics.count) if indices is None else indices
        for index in indices:
            self.hold[index]=0;self.through[index]=False
            self.success_holds[index].reset()
            self.initial_center_x[index]=self.geometric_center(index)[0]
            if self.task=='kick_ball_to_goal':
                self.goal_entries[index].reset(self.geometric_center(index))

    def progress(self,index):
        p,_,corners=self.geometry(index)
        if self.task=='push_box':return push_progress(self.geometric_center(index)[0],self.initial_center_x[index])
        if self.task=='kick_ball_to_goal':
            return float(self.geometric_center(index)[0]-self.initial_center_x[index])
        if self.task=='press_button':
            joint=mujoco.mj_name2id(self.physics.model,mujoco.mjtObj.mjOBJ_JOINT,'button_slide')
            return float(self.physics.data[index].qpos[self.physics.model.jnt_qposadr[joint]])
        return float(corners[:,2].min()-self.profile['floor_z_m'])

    def geometry(self,index):
        d=self.physics.data[index];p=d.xpos[self.body];r=d.xmat[self.body].reshape(3,3)
        if self.task=='push_box':
            bounds=self.profile.get('bounds_local')
            local=np.array(list(itertools.product(*zip(*bounds)))) if bounds is not None else np.array(list(itertools.product(*[[-h,h] for h in self.profile['half_extent']])))
            corners=local@r.T+p
        elif self.task=='lift_basket':
            if 'support_vertices_local' in self.profile:
                local=np.asarray(self.profile['support_vertices_local'])
            else:
                local=np.concatenate([np.array(list(itertools.product(*[[-h,h] for h in part['half_extent']])))+
                                      part['position'] for part in self.profile['parts']])
            corners=local@r.T+p
        else:corners=np.array([p])
        return p,r,corners

    def geometric_center(self,index):
        p,r,corners=self.geometry(index)
        if self.task=='push_box' and 'center_local' in self.profile:
            return p+r@np.asarray(self.profile['center_local'])
        if self.task=='lift_basket':return (corners.min(0)+corners.max(0))/2
        if self.task=='press_button' and 'button_rest_front_xyz' in self.profile:
            result=np.asarray(self.profile['button_rest_front_xyz'],dtype=float).copy()
            result[0]+=self.progress(index)
            return result
        return p

    def evaluate(self,index,core):
        p,r,corners=self.geometry(index)
        fallen=bool(core.base_height[index]<.1 or np.linalg.norm(core.projected_gravity_b[index].cpu().numpy()-[0,0,-1])>.75)
        displacement=0.
        if self.task=='press_button':
            joint=mujoco.mj_name2id(self.physics.model,mujoco.mjtObj.mjOBJ_JOINT,'button_slide')
            displacement=float(self.physics.data[index].qpos[self.physics.model.jnt_qposadr[joint]])
        if self.task=='kick_ball_to_goal':
            condition=self.goal_entries[index].update(int(self.physics.ticks[index]),self.geometric_center(index))
            progress=self.progress(index)
        else:
            condition,progress=physical_condition(self.task,self.profile,corners_world=corners,
                displacement=displacement,time_s=float(self.physics.ticks[index])*.002,
                center_x=self.geometric_center(index)[0],initial_center_x=self.initial_center_x[index])
        hold=self.success_holds[index]
        success=hold.update(int(self.physics.ticks[index]),
                            displacement if self.task=='press_button' else condition,not fallen)
        self.hold[index]=hold.count
        return {'success':bool(success),'fallen':fallen,'progress':progress,
                'timed_out':bool(self.physics.ticks[index]*.002>=self.profile['horizon_s'])}
