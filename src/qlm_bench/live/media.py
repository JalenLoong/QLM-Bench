"""Passive actual-RGB/state evidence; owns no reset, simulator or policy."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from qlm_bench.data.video_writer import VideoSink
from qlm_bench.compatibility.dataset_v2.finalization import finalize_video
from qlm_bench.compatibility.dataset_v2.media import MediaTools
from qlm_bench.compatibility.dataset_v2.validation import PROFILE
from qlm_bench.compatibility.rgb_profiles import dataset_profile, LEGACY_RGB


def compact(value):
    if isinstance(value,np.ndarray):return {'shape':list(value.shape),'dtype':str(value.dtype),'sha256':hashlib.sha256(value.tobytes()).hexdigest()}
    if isinstance(value,dict):return {k:compact(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [compact(v) for v in value]
    if isinstance(value,np.generic):return value.item()
    return value


class ActualRGBRecorder:
    def __init__(self,output,*,ffmpeg,ffprobe,identity,observer=True):
        self.root=Path(output);self.root.mkdir(parents=True,exist_ok=False)
        self.tools=MediaTools(ffmpeg,ffprobe);self.observer=observer
        self.identity=identity;self.epoch=None;self.folder=None;self.sinks={};self.last_tick=None
        self.frames=[];self.episodes=[];self.terminal=None;self.closed=False
        self.frame_errors=[]
        self._write(self.root/'identity.json',identity)

    @staticmethod
    def _write(path,value):
        Path(path).write_text(json.dumps(compact(value),indent=2,allow_nan=False)+'\n')

    def _start(self,snapshot):
        if self.folder is not None:self._finish()
        if snapshot['physics_step']!=0 or snapshot['simulation_time_ns']!=0:
            raise ValueError('Actual media requires the real initial reset boundary')
        self.epoch=snapshot['reset_epoch'];self.folder=self.root/f'epoch_{self.epoch:06d}'
        self.folder.mkdir(exist_ok=False);self.last_tick=None;self.frames=[];self.terminal=None;self.frame_errors=[]
        self.rgb_profile=snapshot.get('rgb_spatial_profile',LEGACY_RGB)
        self.profile=dataset_profile(PROFILE,self.rgb_profile)
        roles=('ego','task_centric','observer') if self.observer else ('ego','task_centric')
        self.sinks={}
        for role in roles:self.sinks[role]=VideoSink(self.folder/(role+'.mp4'),self.tools.ffmpeg,25 if role=='observer' else 50,rgb_profile=LEGACY_RGB if role=='observer' else self.rgb_profile)

    def observe(self,snapshot):
        if self.closed:raise ValueError('Media recorder is closed')
        if snapshot['reset_epoch']!=self.epoch:self._start(snapshot)
        tick=int(snapshot['physics_step'])
        if self.last_tick is not None and tick<=self.last_tick:raise ValueError('Duplicate/stale observation callback')
        if snapshot['simulation_time_ns']!=tick*2_000_000:raise ValueError('Source media clock mismatch')
        rgb=snapshot['rgb'];indices={}
        if set(rgb)!= {'ego','task_centric'}:raise ValueError('Exactly two policy RGB views required')
        if tick%10==0:
            expected=tick//10
            for role,image in rgb.items():
                if self.sinks[role].count!=expected:raise ValueError('Missing source50Hz RGB boundary')
                self.sinks[role].write(image);indices[role]=expected
        if self.observer and tick%20==0:
            image=snapshot.get('observer_rgb')
            if image is None or self.sinks['observer'].count!=tick//20:raise ValueError('Missing original25Hz Observer')
            self.sinks['observer'].write(image);indices['observer']=tick//20
        record={k:v for k,v in snapshot.items() if k not in ('rgb','observer_rgb','executed_history')}
        record.update(video_frame_indices=indices,actual_RGB={role:{'sha256':hashlib.sha256(image.tobytes()).hexdigest(),
            'std':float(image.std()),'shape':list(image.shape)} for role,image in rgb.items()},
            completed_commands=len(snapshot.get('executed_history',[])))
        if tick==0 or tick%200==0:
            for role,image in rgb.items():Image.fromarray(image).save(self.folder/f'{tick:06d}-{role}.png')
        self.frames.append(compact(record));self.last_tick=tick
        with (self.folder/'frames.jsonl').open('a') as stream:stream.write(json.dumps(compact(record),allow_nan=False)+'\n')
        uniform_pair=all(image.std()<1 for image in rgb.values())
        known_grey=any(image.std()<1 and 236<=float(image.mean())<=239 for image in rgb.values())
        if uniform_pair or known_grey:
            for role,image in rgb.items():Image.fromarray(image).save(self.folder/f'invalid-{tick:06d}-{role}.png')
            self.frame_errors.append({'physics_step':tick,'reason':'uniform policy pair or known grey framebuffer output',
                                      'RGB':record['actual_RGB']})
            self._write(self.folder/'frame-errors.json',self.frame_errors)
            raise ValueError('Actual scene visual gate failed; source images retained')

    def seal_terminal(self,snapshot):
        if snapshot['reset_epoch']!=self.epoch:raise ValueError('Terminal belongs to another reset epoch')
        if snapshot['physics_step']!=self.last_tick:raise ValueError('Terminal frame was not captured at its actual boundary')
        if self.terminal is not None:return
        record=compact({k:v for k,v in snapshot.items() if k not in ('rgb','observer_rgb')});record['images']={}
        images={**snapshot['rgb']}
        if snapshot.get('observer_rgb') is not None:images['observer']=snapshot['observer_rgb']
        for role,image in images.items():
            path=self.folder/('terminal-'+role+'.png');Image.fromarray(image).save(path)
            record['images'][role]={'path':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                                    'actual_RGB_sha256':hashlib.sha256(image.tobytes()).hexdigest()}
        self.terminal=record;self._write(self.folder/'terminal.json',record)

    def _finish(self):
        errors=list(self.frame_errors);videos={}
        for role,sink in self.sinks.items():
            try:
                receipt=sink.close()
                validated=finalize_video(Path(receipt['partial']),Path(receipt['final']),count=receipt['count'],
                    fps=25 if role=='observer' else 50,tools=self.tools,profile=None if role=='observer' else self.profile['policy_video'],
                    receipt=None if role=='observer' else receipt['receipt'])
                if validated['episode_status']!='video_validated':raise ValueError(str(validated))
                videos[role]={'path':Path(receipt['final']).name,'frames':receipt['count'],
                              'sha256':hashlib.sha256(Path(receipt['final']).read_bytes()).hexdigest(),'encoding':receipt['receipt']}
            except BaseException as error:errors.append({'role':role,'error':repr(error)})
        result={'passed':not errors and self.terminal is not None,'reset_epoch':self.epoch,'videos':videos,
                'actual_observation_boundaries':len(self.frames),'terminal_before_reset':self.terminal is not None,
                'errors':errors,'kind':'actual_runtime_RGB_and_state_not_reconstruction','formal_demonstration':False}
        self._write(self.folder/'result.json',result);self.episodes.append(result);self.folder=None;self.sinks={}
        if not result['passed']:raise ValueError('Actual media validation failed or pre-reset terminal missing')

    def close(self):
        if self.closed:return
        try:
            if self.folder is not None:self._finish()
        finally:
            self.closed=True
            self._write(self.root/'result.json',{'passed':bool(self.episodes) and all(r['passed'] for r in self.episodes),
                'episodes':self.episodes,'identity':self.identity,'policy_input_views':['ego','task_centric'],
                'observer_role':'diagnostic_only','RGB_source':'actual runtime observation callback'})
