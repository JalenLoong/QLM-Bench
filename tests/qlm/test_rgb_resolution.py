"""Spatial profiles preserve geometry/rates and reject mislabeled RGB."""
from copy import deepcopy
import numpy as np
import pytest
from qlm_bench.compatibility.rgb_profiles import *
from qlm_bench.compatibility.dataset_v2.validation import PROFILE, LOCK
from qlm_bench.compatibility.contracts_v2.validation import BUNDLE
from qlm_bench.live import make_observation, validate_live_observation


def test_immutable_720_and_scaled_calibration():
 old=deepcopy(PROFILE);new=dataset_profile(PROFILE,RGB_360)
 assert digest(PROFILE)==LOCK['profile_hash'] and PROFILE==old
 assert new['policy_video']['fps']==50
 for key in ('go2_ego','d435i_rgb_task'):
  a,b=old['policy_camera_geometry'][key],new['policy_camera_geometry'][key]
  assert (b['height'],b['width'])==(360,640)
  assert np.array_equal(np.asarray(a['intrinsics'])[:2]*.5,np.asarray(b['intrinsics'])[:2])
  assert a['mount_position_m']==b['mount_position_m'] and a['mount_quaternion_xyzw']==b['mount_quaternion_xyzw']
 assert resolve_dataset_profile(PROFILE,digest(new))[1]==RGB_360
 with pytest.raises(ValueError):resolve_dataset_profile(PROFILE,'0'*64)


def test_live_payload_profile_is_explicit():
 state={'observation.state.base.position':[0.,0.,.3], 'observation.state.base.orientation':[0.,0.,0.,1.],
        'observation.state.base.linear_velocity':[0.,0.,0.], 'observation.state.base.angular_velocity':[0.,0.,0.],
        'observation.state.projected_gravity':[0.,0.,-1.]}
 snapshot={'physics_step':0,'simulation_time_ns':0,'reset_epoch':1,'state':state,
           'rgb_spatial_profile':RGB_360,'rgb':{'ego':np.zeros((360,640,3),np.uint8),'task_centric':np.zeros((360,640,3),np.uint8)},
           'sensor_frame_ids':{'ego':0,'task_centric':0}}
 packet=make_observation([snapshot],session_id='session',episode_id='episode',reset_epoch=1,message_id='rgb',instruction='Push the box.',executed_history=[],state_semantics={})
 assert validate_live_observation(packet)['samples'][0]['rgb']['go2_ego'].shape==(360,640,3)
 packet['samples'][0]['rgb']['go2_ego']=np.zeros((720,1280,3),np.uint8)
 with pytest.raises(ValueError):validate_live_observation(packet)


def test_evalcase_spatial_identity_does_not_relabel_old_cases():
 from qlm_bench.backends.mujoco.evaluation import case_rgb_profile
 assert case_rgb_profile(PROFILE['policy_camera_geometry'])==LEGACY_RGB
 cameras=dataset_profile(PROFILE,RGB_360)['policy_camera_geometry']
 assert case_rgb_profile(cameras)==RGB_360
 cameras['go2_ego']['intrinsics'][0][0]+=1
 with pytest.raises(ValueError):case_rgb_profile(cameras)
