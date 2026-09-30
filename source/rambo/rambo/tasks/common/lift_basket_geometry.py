"""Exact rigid mesh extrema from convex-hull support vertices; CPU geometry."""
import numpy as np
from .push_box_geometry import rotation_xyzw

def world_geometry(vertices, pose):
    vertices=np.asarray(vertices,dtype=np.float64);pose=np.asarray(pose,dtype=np.float64)
    if vertices.ndim!=2 or vertices.shape[1]!=3 or not np.isfinite(vertices).all():raise ValueError('Invalid vertices')
    world=vertices@rotation_xyzw(pose[3:]).T+pose[:3]
    low=world.min(0);high=world.max(0)
    return dict(center=((low+high)/2).tolist(),minimum_world_z=float(low[2]),maximum_world_z=float(high[2]),bounds_world=[low.tolist(),high.tolist()])

def lifted(geometry, floor_z=0., minimum=.06):
    return geometry['minimum_world_z']-floor_z>=minimum


def completely_through(foot_center, foot_radius, handle_vertices, axis, margin):
    axis=np.asarray(axis,dtype=float);axis=axis/np.linalg.norm(axis)
    far=float(np.max(np.asarray(handle_vertices)@axis))
    rear=float(np.asarray(foot_center)@axis)-float(foot_radius)
    return rear>=far+margin, rear-far

def ego_projection(points, root_pose, margin=8):
    from .lift_camera_rig import camera_world_transform,CAMERAS
    eye,R=camera_world_transform(root_pose,'ego');p=(np.asarray(points)-eye)@R
    m=CAMERAS['ego'];fx=m['width']*m['focal_length_mm']/m['horizontal_aperture_mm'];fy=m['height']*m['focal_length_mm']/m['vertical_aperture_mm']
    depth=p[:,0];safe=np.where(depth>.0001,depth,.0001)
    uv=np.column_stack([m['width']/2-fx*p[:,1]/safe,m['height']/2-fy*p[:,2]/safe])
    visible=bool(np.all(depth>.005) and np.all(uv[:,0]>=margin) and np.all(uv[:,0]<=m['width']-margin) and np.all(uv[:,1]>=margin) and np.all(uv[:,1]<=m['height']-margin))
    return dict(in_frustum=visible,uv_min=uv.min(0).tolist(),uv_max=uv.max(0).tolist(),minimum_depth_m=float(depth.min()),occlusion_checked=False)
