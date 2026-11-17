"""User-authorized physical socket-exit criterion; no simulator or controller writes."""
import itertools
import numpy as np
import mujoco

PROFILE_ID='door-socket-clear-open15deg-v3'

class DoorSocketExit:
    def __init__(self,model,profile):
        self.model,self.profile=model,profile
        prefix=profile['bolt_joint'].removesuffix('_bolt_joint')
        self.frame=model.body(prefix+'_frame').id
        self.shaft=model.geom(prefix+'_bolt_shaft').id
        self.walls=[model.geom(prefix+'_strike_'+axis+'wall_'+side).id
                    for axis in ['x','z'] for side in ['-1','1']]
        assert model.geom_type[self.shaft]==mujoco.mjtGeom.mjGEOM_BOX
        assert all(model.geom_bodyid[g]==self.frame for g in self.walls)
        assert all(np.allclose(model.geom_quat[g],[1,0,0,0],rtol=0,atol=1e-12) for g in self.walls)
        self.mouth_y=max(model.geom_pos[g,1]+model.geom_size[g,1] for g in self.walls)
        self.local_corners=np.array(list(itertools.product([-1,1],repeat=3)))*model.geom_size[self.shaft]
        self.address={key:int(model.joint(profile[key]).qposadr[0]) for key in ['bolt_joint','lever_joint','primary_joint']}
        self.unlocked=False

    def reset(self):self.unlocked=False

    def observe(self,data):
        world=self.local_corners@data.geom_xmat[self.shaft].reshape(3,3).T+data.geom_xpos[self.shaft]
        local=(world-data.xpos[self.frame])@data.xmat[self.frame].reshape(3,3)
        gap=float(local[:,1].min()-self.mouth_y)
        bolt=float(data.qpos[self.address['bolt_joint']]);lever=float(data.qpos[self.address['lever_joint']]);door=float(data.qpos[self.address['primary_joint']])
        event=bool(gap>=0. and bolt>0. and lever<=self.profile['unlock_lever_max_rad'])
        self.unlocked=self.unlocked or event
        return dict(socket_exit_clearance_m=gap,bolt_retraction_m=bolt,lever_rad=lever,door_rad=door,
                    geometric_unlock_event=event,unlocked_history=self.unlocked,
                    condition=bool(self.unlocked and door>=self.profile['target_open_rad']))


# Exact predicate port; source SHA256: f9a1ff76fb03e9230729c8f59f4dbff036ab7032783142151e3c879c51a6772d
