"""Native9 high-level door trajectories; no object/controller/physics mutations."""
import math
import json
import numpy as np
import mujoco
from shared_executor import SmoothReference
from qlm_bench.backends.mujoco.press_reference_smooth import blend


def rz(q):
    c,s=math.cos(q),math.sin(q)
    return np.array([[c,-s,0],[s,c,0],[0,0,1.]])


def ry(q):
    c,s=math.cos(q),math.sin(q)
    return np.array([[c,0,s],[0,1,0],[-s,0,c]])


class Fridge(SmoothReference):
    def configure(self):
        self.pivot=self.runtime.physics.model.body('primary').pos.copy()
        self.fixture_rot=np.zeros(9);mujoco.mju_quat2Mat(self.fixture_rot,self.runtime.physics.model.body('primary').quat);self.fixture_rot=self.fixture_rot.reshape(3,3)
        self.start_angle=float(self.runtime.task.progress(0))
        self.radius=self.config.get('panel_radius_m',.40)
        self.height=self.config.get('contact_height_m',.28)
        self.forward=self.config.get('working_forward_m',.28)
        self.lateral=self.config.get('working_lateral_m',.18)
        self.standoff=self.point(self.start_angle,self.config.get('standoff_local_x_m',-.065))
        self.final_base_goal=self.standoff[:2]-[self.forward,self.lateral]
        self.final_base_goal[1]=self.point(self.start_angle)[1]-self.lateral
        self.base_goal=np.array([min(-.02,float(self.core.robot.position[0,0])),self.final_base_goal[1]])
        self.forward_settled_since=None
        self.door_operation_start=None

    def point(self,q,x=-.035):
        return self.pivot+self.fixture_rot@rz(q)@np.array([x,-self.radius,self.height-self.pivot[2]])

    def interaction(self,age,t,dt):
        if self.door_operation_start is None:
            self.phase='position_forward_beside_door'
            self.base_goal=self.final_base_goal.copy()
            error=np.max(np.abs(self.base_goal-self.base_feedback))
            if error<.018:
                if self.forward_settled_since is None:self.forward_settled_since=t
                if t-self.forward_settled_since>=.4:
                    self.door_operation_start=t
                    self.door_operation_world_start=self.actual_world_point().copy()
            else:self.forward_settled_since=None
            return self.world_body_point(self.config['carry_body_xyz_m'])
        age=t-self.door_operation_start
        present=self.config.get('present_seconds',1.8)
        contact=self.config.get('contact_seconds',1.2)
        closing=self.config.get('closing_seconds',10.)
        if age<present:
            self.phase='present_panel'
            return self.door_operation_world_start+(self.standoff-self.door_operation_world_start)*blend(age/present)
        if age<present+contact:
            self.phase='contact_panel'
            end=self.point(self.start_angle)
            return self.standoff+(end-self.standoff)*blend((age-present)/contact)
        self.phase='push_closing_arc'
        q=self.start_angle+(self.config.get('target_angle_rad',.025)-self.start_angle)*blend((age-present-contact)/closing)
        target=self.point(q,self.config.get('contact_local_x_m',-.035))
        self.base_goal=target[:2]-[self.forward,self.lateral]
        return target


class Oven(SmoothReference):
    def configure(self):
        self.pivot=self.runtime.physics.model.body('primary').pos.copy()
        self.fixture_rot=np.zeros(9);mujoco.mju_quat2Mat(self.fixture_rot,self.runtime.physics.model.body('primary').quat);self.fixture_rot=self.fixture_rot.reshape(3,3)
        self.contact_y=self.config.get('contact_y_m',-.27)
        self.panel_z=self.config.get('panel_height_local_m',.20)
        self.forward=self.config.get('working_forward_m',.28)
        self.lateral=self.config.get('working_lateral_m',.18)
        self.open_angle=self.config.get('operation_start_angle_rad',-math.pi/2)
        self.under=self.point(self.open_angle)
        rail=self.runtime.physics.model.geom('close_oven_door_top_rail')
        door_height=float(rail.pos[2]+rail.size[2])
        self.outside=self.pivot+self.fixture_rot@np.array([-door_height-self.config.get('front_entry_standoff_m',.065),self.contact_y,self.under[2]-self.pivot[2]])
        self.above=self.outside.copy();self.above[2]=self.config.get('side_clearance_height_m',.22)
        self.base_goal=self.under[:2]-[self.forward,self.lateral]
        self.last_contact_second=-1

    def point(self,q):
        cosine=max(math.cos(q),.0001)
        x=self.config.get('contact_local_x_m',-.038)
        # Initial long lever; slide toward the hinge only as needed to keep the
        # foot physically reachable below the original Go2 shoulder height.
        cap=self.config.get('maximum_contact_world_height_m',.21)
        reachable=(cap-self.pivot[2]+math.sin(q)*x)/cosine
        panel_z=float(np.clip(reachable,self.config.get('closing_contact_height_local_m',.09),self.panel_z))
        return self.pivot+self.fixture_rot@ry(q)@np.array([self.config.get('contact_local_x_m',-.038),self.contact_y,panel_z])

    def interaction(self,age,t,dt):
        present=self.config.get('present_seconds',1.6)
        lower=self.config.get('lower_seconds',1.6)
        insert=self.config.get('insert_seconds',1.5)
        closing=self.config.get('closing_seconds',10.)
        if age<present:
            self.phase='present_side'
            return self.interaction_world_start+(self.above-self.interaction_world_start)*blend(age/present)
        if age<present+lower:
            self.phase='lower_outside'
            return self.above+(self.outside-self.above)*blend((age-present)/lower)
        if age<present+lower+insert:
            self.phase='insert_under_panel'
            return self.outside+(self.under-self.outside)*blend((age-present-lower)/insert)
        self.phase='lift_closing_arc'
        actual_q=float(self.runtime.task.progress(0))
        q=min(self.config.get('target_angle_rad',.02),actual_q+self.config.get('angle_lead_rad',.08))
        target=self.point(q)
        self.base_goal=target[:2]-[self.forward,self.lateral]
        return target

    def command(self):
        values,diag=super().command()
        t=float(self.runtime.physics.ticks[0])*.002
        if int(t)!=self.last_contact_second:
            self.last_contact_second=int(t)
            d=self.runtime.physics.data[0];m=self.runtime.physics.model;p=m.body('primary').id;contacts=[]
            for i in range(d.ncon):
                c=d.contact[i];a,b=int(c.geom1),int(c.geom2)
                if p in (int(m.geom_bodyid[a]),int(m.geom_bodyid[b])):
                    force=np.zeros(6);mujoco.mj_contactForce(m,d,i,force)
                    contacts.append({'geoms':[m.geom(a).name,m.geom(b).name],
                        'normal_world':c.frame.reshape(3,3)[0].tolist(),'normal_force_N':float(force[0])})
            print(json.dumps({'physical_contact_diagnostic':True,'time_s':t,'actual_q_rad':float(self.runtime.task.progress(0)),
                              'contacts':contacts,'stage':self.phase}),flush=True)
        return values,diag
