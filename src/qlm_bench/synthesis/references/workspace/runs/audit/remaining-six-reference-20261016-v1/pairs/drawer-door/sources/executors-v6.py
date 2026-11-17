"""Bounded high-level native9 recipes; never writes physics/controller internals."""
import numpy as np
import json
from shared_executor import SmoothReference,blend


def interp(a,b,age,duration):
    return np.asarray(a)+(np.asarray(b)-np.asarray(a))*blend(age/duration)


class DrawerExecutor(SmoothReference):
    def configure(self):
        self.config['recipe_id']='drawer-underhook-base-lead-slow-pull-v5'
        self.model=self.runtime.physics.model
        self.prefix='drawer_a'
        self.bar_id=self.model.geom(self.prefix+'_handle_bar').id
        self.bar0=self.runtime.physics.data[0].geom_xpos[self.bar_id].copy()
        self.base0=np.array([self.bar0[0]-.43,self.bar0[1]-.14])
        self.base_goal=self.base0.copy()
        self.pull_start=None;self.hook_ready_ticks=0;self.diag_tick=-1;self.segment='settle'

    def interaction(self,age,t,dt):
        bar=self.bar0
        below=bar+np.array([.078,0,-.080])
        inserted=bar+np.array([.078,0,.015])
        if age<2.0:return interp(self.interaction_world_start,below,age,2.)
        if age<4.0:return interp(below,inserted,age-2.,2.)
        if self.pull_start is None:
            actual=self.actual_world_point()
            good=actual[2]>=bar[2]-.005 and actual[0]>=bar[0]+.045 and abs(actual[1]-bar[1])<.035
            self.hook_ready_ticks=self.hook_ready_ticks+1 if good else 0
            self.segment='insert_and_confirm_actual_pose'
            if self.hook_ready_ticks>=3:self.pull_start=age
            return inserted
        self.segment='pull'
        pull_age=age-self.pull_start
        if pull_age<1.:return interp(inserted,bar+[.030,0,.015],pull_age,1.)
        u=blend((pull_age-1.)/16.)
        self.base_goal=self.base0-np.array([.245*u+.050*blend(pull_age/2.),0])
        return bar+np.array([.030-.245*u,0,.015])

    def command(self):
        values,diag=super().command();tick=int(self.runtime.physics.ticks[0])//250
        if tick!=self.diag_tick:
            self.diag_tick=tick;d=self.runtime.physics.data[0];m=self.runtime.physics.model
            contacts=[]
            for c in d.contact:
                a=m.geom(int(c.geom1)).name;b=m.geom(int(c.geom2)).name
                if 'drawer_a_' in a or 'drawer_a_' in b:contacts.append([a,b])
            print(json.dumps({'drawer_diagnostic':True,'t':float(d.time),'segment':self.segment,
                              'wanted_world':diag.get('unprojected_world_target'),'projected_world':diag.get('world_target'),
                              'reference_joints':diag.get('reference_geometric_joints_rad'),'actual_world':self.actual_world_point().tolist(),
                              'contacts':contacts}),flush=True)
        return values,diag


class DoorExecutor(SmoothReference):
    def configure(self):
        self.config['recipe_id']='door-real-cam-reachable-lateral-push-v2'
        self.origin=self.runtime.physics.data[0].xpos[self.runtime.physics.model.body('primary').id].copy()
        self.base0=np.array([self.origin[0]-.50,self.origin[1]-.53])
        self.base_goal=self.base0.copy()
        self.unlock_time=None;self.unlock_ticks=0;self.press_extra=0.;self.diag_tick=-1;self.segment='settle'

    def handle(self,door_angle,lever_angle):
        loc=np.array([-.058,-.52+.090*np.cos(lever_angle),.350+.090*np.sin(lever_angle)])
        c,s=np.cos(door_angle),np.sin(door_angle)
        return self.origin+np.array([c*loc[0]-s*loc[1],s*loc[0]+c*loc[1],loc[2]])

    def interaction(self,age,t,dt):
        pre=self.handle(0,0)+np.array([-.065,0,.015])
        if age<2.0:return interp(self.interaction_world_start,pre,age,2.)
        if age<3.0:return interp(pre,self.handle(0,0)+[-.008,0,.019],age-2.,1.)
        lever=-np.deg2rad(35.)*blend((age-3.)/4.)
        point=self.handle(0,lever)
        # Lateral base/FL coordination keeps the original IK branch reachable
        # while the handle goes from high neutral to low fully depressed.
        lateral=.10+.04*blend((age-3.)/4.)
        self.base_goal=np.array([self.base0[0],point[1]-lateral])
        d=self.runtime.physics.data[0];m=self.runtime.physics.model
        qlever=float(d.qpos[int(m.joint('door_a_lever_joint').qposadr[0])])
        qbolt=float(d.qpos[int(m.joint('door_a_bolt_joint').qposadr[0])])
        good=qbolt>=.020 and qlever<=-np.deg2rad(20.)
        self.unlock_ticks=self.unlock_ticks+1 if good else 0
        if self.unlock_time is None and self.unlock_ticks>=3:self.unlock_time=t
        if self.unlock_time is None or t-self.unlock_time<.4:
            self.segment='press_real_lever_and_wait_for_actual_bolt'
            if age>7.:self.press_extra=min(.006,self.press_extra+.0005*dt)
            return point+np.array([-.008,0,.019-self.press_extra])
        self.segment='push_real_door_arc'
        theta=np.deg2rad(65.)*blend((t-self.unlock_time-.4)/14.)
        point=self.handle(theta,-np.deg2rad(35.))
        self.base_goal=point[:2]-np.array([.435,.14])
        return point+np.array([-.008,0,.015])

    def command(self):
        values,diag=super().command();tick=int(self.runtime.physics.ticks[0])//250
        if tick!=self.diag_tick:
            self.diag_tick=tick;d=self.runtime.physics.data[0];m=self.runtime.physics.model
            names=['door_a_hinge','door_a_lever_joint','door_a_bolt_joint']
            q={n:float(d.qpos[int(m.joint(n).qposadr[0])]) for n in names}
            contacts=[]
            for c in d.contact:
                a=m.geom(int(c.geom1)).name;b=m.geom(int(c.geom2)).name
                if ('door_a_' in a or 'door_a_' in b) and not ('eccentric_cam' in a or 'eccentric_cam' in b):contacts.append([a,b])
            print(json.dumps({'door_diagnostic':True,'t':float(d.time),'segment':self.segment,'joints':q,
                              'wanted_world':diag.get('unprojected_world_target'),'projected_world':diag.get('world_target'),
                              'actual_world':self.actual_world_point().tolist(),'contacts':contacts}),flush=True)
        return values,diag
