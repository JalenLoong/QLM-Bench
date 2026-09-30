import numpy as np
from scipy.spatial import ConvexHull
from rambo.tasks.common.lift_basket_geometry import world_geometry,lifted
from rambo.tasks.common.push_box_geometry import PolicySuccessHold

def test_centroid_height_cannot_replace_minimum_geometry():
    points=np.array([[0,0,-.1],[.1,0,.1],[0,.1,.1],[-.1,-.1,.1]])
    g=world_geometry(points,[0,0,.15,0,0,0,1])
    assert g['center'][2]>.06 and not lifted(g)
    assert lifted(world_geometry(points,[0,0,.161,0,0,0,1]))

def test_hull_extrema_equal_all_vertices_under_tilt():
    points=np.random.default_rng(42).normal(size=(1000,3))*.1
    hull=points[ConvexHull(points).vertices]
    for _ in range(20):
        q=np.random.default_rng(_).normal(size=4);q/=np.linalg.norm(q)
        assert np.isclose(world_geometry(points,[0,0,.2,*q])['minimum_world_z'],world_geometry(hull,[0,0,.2,*q])['minimum_world_z'])

def test_three_consecutive_policy_ticks_and_fall_reset():
    h=PolicySuccessHold(3)
    assert not h.update(10,True,True)
    assert not h.update(20,True,False)
    assert not h.update(30,True,True)
    assert not h.update(40,True,True)
    assert h.update(50,True,True)
    h.reset();assert not h.update(60,True,True)


def test_complete_thread_requires_entire_foot_after_far_face():
    from rambo.tasks.common.lift_basket_geometry import completely_through
    handle=np.array([[.74,.1,.2],[.76,.2,.29]])
    assert not completely_through([.77,.15,.22],.025,handle,[1,0,0],.008)[0]
    assert completely_through([.794,.15,.22],.025,handle,[1,0,0],.008)[0]

def test_two_centimeter_threshold_keeps_actual_minimum():
    points=np.array([[0,0,0],[.1,.1,.1],[-.1,-.1,.1]])
    assert not lifted(world_geometry(points,[0,0,.019,0,0,0,1]),minimum=.02)
    assert lifted(world_geometry(points,[0,0,.021,0,0,0,1]),minimum=.02)
