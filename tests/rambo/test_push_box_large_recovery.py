import numpy as np
from rambo.tasks.common.push_box_large_recovery import relationship,visibility,ray_side
from rambo.tasks.common.push_box_geometry import source_geometry


def major_case():
    lo=[.9585,.3279];hi=[1.3143,.5727]
    return {'center':[1.1364,.4503,.1049],
        'footprint_xy':[[lo[0],lo[1]],[hi[0],lo[1]],[hi[0],hi[1]],[lo[0],hi[1]]],
        'projected_box_corners':[[x,y] for x in (lo[0],hi[0]) for y in (lo[1],hi[1])]*2}


def test_major_case_is_mostly_outside_y_despite_being_inside_x():
    g=major_case();p={'goal_x':[.95,1.35],'goal_y':[-.1,.4]}
    lo,hi,x,y=relationship(g,p)
    assert x==1. and y<.3 and hi[1]-.4>.17


def test_back_left_pose_restores_joint_visibility_with_original_camera_calibration():
    g=major_case();p={'goal_x':[.95,1.35],'goal_y':[-.1,.4]}
    before=visibility([.8,.04,.3,0.,0.,0.,1.],g,p)
    after=visibility([.5,.28,.3,0.,0.,0.,1.],g,p)
    assert not any(v['geometric_relationship_visible'] for v in before.values())
    assert after['task']['geometric_relationship_visible']


def test_upper_contact_ray_hits_upper_face_instead_of_rear_face():
    geom=source_geometry([-.15,-.09,-.1],[.15,.09,.1])
    point=ray_side(geom,[1.1,.45,.12,0.,0.,0.,1.],[0.,1.,0.])
    assert np.allclose(point,[1.1,.54,.12])
