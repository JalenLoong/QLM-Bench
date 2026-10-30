"""Single CPU anchor worker over bounded lossless JSON frames on stdin and a private stdout pipe copy."""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import struct
import sys

from qlm_bench.live.transport import dumps,loads,MAX_FRAME_BYTES


def read_frame(stream):
    header=stream.read(4)
    if not header:return None
    if len(header)!=4:raise EOFError('Incomplete IPC header')
    count=struct.unpack('!I',header)[0]
    if not 0<count<=MAX_FRAME_BYTES:raise ValueError('IPC frame bound exceeded')
    payload=bytearray()
    while len(payload)<count:
        block=stream.read(count-len(payload))
        if not block:raise EOFError('Incomplete IPC payload')
        payload.extend(block)
    return loads(bytes(payload))


def write_frame(stream,value):
    raw=dumps(value)
    if len(raw)>MAX_FRAME_BYTES:raise ValueError('IPC response bound exceeded')
    stream.write(struct.pack('!I',len(raw)));stream.write(raw);stream.flush()


class AnchorWorker:
    def __init__(self,binding,reference,verification,controller):
        if os.environ.get('MUJOCO_GL')!='osmesa' or os.environ.get('CUDA_VISIBLE_DEVICES')!='':
            raise ValueError('Explicit CPU-only OSMesa process required')
        import torch
        torch.set_num_threads(1)
        if torch.cuda.is_available():raise ValueError('CPU worker still exposes an accelerator')
        from qlm_bench.backends.factory import create_runtime
        from qlm_bench.backends.mujoco.rl_v2.snapshot import load,restore
        self.load,self.restore=load,restore
        b=json.loads(Path(binding).read_text());self.reference=Path(reference).resolve()
        checked=json.loads(Path(verification).read_text());result=json.loads((self.reference/'result.json').read_text())
        if not checked.get('passed') or not result['passed'] or checked['all_admitted_anchors']!=result['valid_full_groups']:
            raise ValueError('Verified CPU reference/anchor coverage required')
        from qlm_bench.backends.mujoco.rl_v2.storage import sha256
        if (sha256(self.reference/'result.json')!=checked.get('reference_result_sha256') or
                sha256(binding)!=result['binding_sha256']):
            raise ValueError('Reference verification/binding belongs to another replay')
        self.anchor_count=result['valid_full_groups']
        scene=b['scene'];self.runtime=create_runtime(b['episode']['task'],'native',model_path=b['model'],checkpoint=controller,trace_only=False,device='cpu',
            seed=scene['seed'],rgb_profile='dual-rgb-360p-v1',profile_override={k:scene[k] for k in
               ('goal_x','goal_y','canonical_goal_position') if k in scene})
        self.runtime.renderer.observer_clip=None;self.runtime.observation_ticks=40  # RGB is read only at the 80ms reward/model grid.
        if not any(k in self.runtime.renderer.gl_identity['renderer'].lower() for k in ('llvmpipe','softpipe','swrast')):
            raise ValueError('Worker software renderer not verified')
        if self.runtime.renderer.gl_identity!=result['software_renderer']:
            # A different llvmpipe build/SIMD width is recorded, not a reason to redo prepare;
            # the software-renderer requirement above and the RGB reward itself still apply.
            import sys
            print(f"WARNING: software renderer {self.runtime.renderer.gl_identity} differs from reference {result['software_renderer']}",file=sys.stderr,flush=True)
        self.session=None;self.poisoned=False;self.ended=False;self.anchor_tick=None;self.chunk=0
        self.seen={};self.last_id=None;self.last_response=None

    def handle(self,request):
        if set(request)!={'schema','id','operation','session','payload'} or request['schema']!='qlm-rl-v2-ipc-v1':
            raise ValueError('Invalid RL worker envelope')
        key=request['id'];fingerprint=hashlib.sha256(dumps(request)).hexdigest()
        if not isinstance(key,str) or not key or not isinstance(request['session'],str) or not request['session']:
            raise ValueError('Explicit request/session IDs required')
        if key in self.seen:
            if self.seen[key]!=fingerprint:raise ValueError('Conflicting duplicate request')
            if key!=self.last_id:raise ValueError('Response expired; never reexecute physical work')
            return self.last_response
        if len(self.seen)>=10000:raise RuntimeError('Worker request budget exhausted')
        self.seen[key]=fingerprint
        try:
            with contextlib.redirect_stdout(sys.stderr):
                value=self._dispatch(request)
            response={'ok':True,'result':value}
        except Exception as exc:
            self.poisoned=True
            response={'ok':False,'error_type':type(exc).__name__,'error':str(exc)}
        self.last_id=key;self.last_response=response
        return response

    def _dispatch(self,request):
        from qlm_bench.compatibility.contracts_v2.runtime import prepare_command
        rt=self.runtime;op=request['operation'];payload=request['payload']
        if op=='restore':
            if request['session']==self.session:raise ValueError('Anchor restoration requires a new session')
            group=payload['anchor']
            if type(group)is not int or not 0<=group<self.anchor_count:raise ValueError('Anchor not admitted')
            receipt=self.restore(rt,self.load(self.reference/f'anchors/{group:05d}.pt'))
            self.session=request['session'];self.anchor_tick=group*160;self.chunk=0;self.poisoned=False;self.ended=False
            self.last_rgb=rt.state()['rgb']
            return {'anchor':group,'absolute_tick':self.anchor_tick,'relative_tick':0,
                    'restore_epoch':receipt['restore_epoch'],'rgb':self.last_rgb,
                    'freeze':rt.freeze_token(),'renderer':rt.renderer.gl_identity}
        if self.poisoned or request['session']!=self.session:raise ValueError('New anchor session required')
        if op=='inspect':return {'absolute_tick':int(rt.physics.ticks[0]),'freeze':rt.freeze_token()}
        if op!='execute':raise ValueError('Unknown RL environment operation')
        actions=payload['commands']
        if len(actions)!=16 or payload['chunk']!=self.chunk or rt.terminal is not None or self.ended:
            raise ValueError('Exactly one ordered native9 chunk required')
        import numpy as np
        requested=np.asarray(actions,dtype=np.float64)
        if requested.shape!=(16,9) or not np.isfinite(requested).all():raise FloatingPointError('Nonfinite/malformed policy commands')
        start=int(rt.physics.ticks[0])
        if np.max(np.abs(requested))>np.finfo(np.float32).max:
            self.ended=True;state=rt.state()
            terminal={'tick':start,'reason':'policy_command_rejected','policy_failure':True,'task_terminal':False,
                      'success':False,'fallen':False,'timed_out':False,'rgb':state['rgb'],'captured_before_reset':True}
            return {'schema':'qlm-rl-v2-execution-v1','session':self.session,'start_tick':start,'end_tick':start,
                    'relative_end_tick':start-self.anchor_tick,'commands':[],'requested':actions,'completed_count':0,
                    'samples':[],'terminal':terminal,'freeze':rt.freeze_token()}
        prepared=[prepare_command(x,f'{self.session}:{self.chunk}:{i}',start+i*10) for i,x in enumerate(actions)]
        samples=[];terminal=None;rows=[]
        for command in prepared:
            try:outcome=rt.step(command)
            except FloatingPointError as exc:
                # Physics made unstable by the policy's own commands fails this candidate, not the
                # run; the diverged state is never rendered and the next candidate restores an anchor.
                terminal={'tick':int(rt.physics.ticks[0]),'reason':'physics_instability','policy_failure':True,
                          'task_terminal':False,'success':False,'fallen':False,'timed_out':False,
                          'rgb':self.last_rgb,'captured_before_reset':True,'detail':str(exc)}
                break
            rows.append(outcome['command']);tick=int(rt.physics.ticks[0])
            # A terminal exactly on the reward grid is still a real observed sample.
            if tick%40==0:
                samples.append({'tick':tick,'simulation_time_ns':tick*2_000_000,'rgb':rt.state()['rgb']})
                self.last_rgb=samples[-1]['rgb']
            if outcome['terminal'] is not None:
                terminal={'tick':tick,'reason':outcome['terminal']['reason'],
                          **rt.outcome,'rgb':rt.state()['rgb'],'captured_before_reset':True}
                break
        self.ended=terminal is not None
        rows+=prepared[len(rows):]
        self.chunk+=1
        return {'schema':'qlm-rl-v2-execution-v1','session':self.session,'start_tick':start,
                'end_tick':int(rt.physics.ticks[0]),'relative_end_tick':int(rt.physics.ticks[0])-self.anchor_tick,
                'commands':rows,'completed_count':sum(x['status']=='completed' for x in rows),
                'samples':samples,'terminal':terminal,'freeze':rt.freeze_token()}

    def close(self):self.runtime.close()


def protocol_stdout():
    """Frames go to a private copy of the stdout pipe; fd 1 then points at stderr, so C-level
    prints (libmujoco WARNING, Mesa) reach the worker log instead of the frame stream."""
    sys.stdout.flush()
    channel=os.fdopen(os.dup(1),'wb')
    os.dup2(2,1)
    return channel


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('binding','reference','verification','controller'):p.add_argument('--'+name,required=True)
    a=p.parse_args()
    channel=protocol_stdout()  # Before AnchorWorker loads MuJoCo/OSMesa.
    with contextlib.redirect_stdout(sys.stderr):worker=AnchorWorker(**vars(a))
    try:
        while (request:=read_frame(sys.stdin.buffer)) is not None:
            write_frame(channel,worker.handle(request))
    finally:worker.close()


if __name__=='__main__':main()
