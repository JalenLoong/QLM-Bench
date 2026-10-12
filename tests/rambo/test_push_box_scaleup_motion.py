import numpy as np
from rambo.tasks.common.push_box_scaleup_motion import reference
from rambo.tasks.common.push_box_goal_recovery import bounds,reference as repair_reference


EXPERT={'settle_seconds':2.1,'normal_approach_seconds':1.,'face_distance_for_foot_approach':.405,
    'approach_foot_x':.28,'push_foot_x':.38,'penetration_m':.015,'align_base_speed':.14,
    'push_base_speed':.12,'transition_s':.45,'lateral_tracking_gain':2.,'lateral_tracking_limit_m':.015}


def test_contact_to_push_keeps_existing_world_contact_instead_of_nominal_approach_x():
    base=np.array([.59,0.,.3]);previous=np.array([1.015,.15,.12])
    state={'stage':'normal_approach','contact_start':3.74,'contact_target':np.array([.9,.15,.12]),
        'contact_velocity':.14,'last_target':previous.copy(),'last_vx':0.}
    target,vx,vy,phase,info=reference(state,4.74,base=base,neutral=base+np.array([.1934,.142,-.25]),
        ray=[1.,.15,.12],normal=[-1.,0.,0.],actual=previous,expert=EXPERT)
    assert phase=='straight_push' and np.linalg.norm(target-previous)<.001
    assert target[0]-base[0]>.42 and vx==0 and vy==0
    # The foot remains at the existing contact while the body catches up.
    for tick in range(1,36):
        base[0]+=vx*.02
        after,vx,vy,phase,info=reference(state,4.74+tick*.02,base=base,
            neutral=base+np.array([.1934,.142,-.25]),ray=[1.,.15,.12],normal=[-1.,0.,0.],actual=target,expert=EXPERT)
        assert after[0]>=previous[0]-1e-8 and np.linalg.norm(after-target)<.01
        target=after


def geometry(side):
    ys=[.1,.43] if side>0 else [-.13,.2]
    return {'footprint_xy':[[.96,ys[0]],[1.18,ys[0]],[1.18,ys[1]],[.96,ys[1]]],
        'center':[1.07,sum(ys)/2,.11]}


def profile(side):
    return {'goal_x':[.95,1.35],'goal_y':[-.1,.4],'initial_center_x_world':.69,
        'scaleup_goal_recovery':{'side':side}}


def test_small_upper_and_lower_overflow_are_equivalent_trigger_cases():
    for side in (-1,1):
        lo,hi,excess,overlap,ready=bounds(geometry(side),profile(side),side)
        assert ready and np.isclose(excess,.03) and overlap>.9
        distant={**geometry(side),'footprint_xy':[[.5,.1],[.8,.1],[.8,.43],[.5,.43]]}
        assert not bounds(distant,profile(side),side)[-1]
        large={**geometry(side),'footprint_xy':[[.96,-.3],[1.18,-.3],[1.18,.6],[.96,.6]]}
        assert not bounds(large,profile(side),side)[-1]


def test_stop_command_alone_does_not_certify_actual_braking():
    state={};g=geometry(1);p=profile(1);base=[.63,.06,.3];target=[.98,.265,.11]
    for time in (10.,10.36,10.38,10.4,11.):
        result=repair_reference(state,time,geometry=g,profile=p,base=base,actual=target,
            actual_velocity=[.12,0.,0.],target=target,vx=.12)
    assert result[1]==0. and result[-1]['braked_actual_forward_velocity'] is False


def test_measured_side_shift_and_inward_stroke_mirror_across_y_sides():
    for side in (-1,1):
        state={};g=geometry(side);p=profile(side);base=np.array([.63,.06 if side>0 else -.115,.3]);target=np.array([.98,g['center'][1],.11])
        def step(time,position):
            return repair_reference(state,time,geometry=g,profile=p,base=position,actual=target,
                actual_velocity=[0.,0.,0.],target=target,vx=.12)
        step(10.,base);step(10.36,base);step(10.38,base);r=step(11.,base)
        assert r[1]==0. and side*r[2]>0 and r[-1]['braked_actual_forward_velocity']
        surface=.43 if side>0 else -.13;shifted=base.copy();shifted[1]=surface+side*.03-.142
        step(13.7,shifted);r0=step(14.6,shifted);r1=step(15.8,shifted)
        assert r1[3]=='goal_recovery_inward_push' and side*(r1[0][1]-r0[0][1])<0
        assert r1[-1]['body_shift_signed_m']>.05 and r1[-1]['inward_stroke']
