"""Public 2.0 acknowledgement consumer, independent of simulator scheduling.

Extracted unchanged from the original WAM contracts_v2 consumer ledger (INFER-001);
only the validator import is redirected to the public frozen compatibility package.
"""
from __future__ import annotations
import copy
import numpy as np
from qlm_bench.compatibility.contracts_v2.validation import (CAMERAS, ContractError, require, digest, validate_record,
                         validate_profiles, validate_command, validate_frame)


class PolicyHistory:
    def __init__(self, *, cache_resetters=()):
        self.resetters=tuple(cache_resetters);self.identity=None;self.records=[];self.pending=None
        self.tick=0;self.last_capture=None;self.observation_id=None;self.acks={};self.state='NEW'

    def _check(self, message, kind):
        validate_record(kind,message);validate_profiles(message['profiles'])
        require((message['session_id'],message['episode_id'],message['reset_epoch'])==self.identity,'epoch','history epoch')

    def reset(self, request):
        validate_record('ResetRequest',request);validate_profiles(request['profiles'])
        ident=(request['session_id'],request['episode_id'],request['reset_epoch'])
        if ident==self.identity and request['message_id']==getattr(self,'reset_id',None):
            require(digest(request)==self.reset_digest,'duplicate','conflicting reset')
            return
        require(self.identity is None or ident[0]!=self.identity[0] or ident[2]>self.identity[2],'epoch','reset must advance')
        self.state='ERROR'
        for reset in self.resetters:reset()
        self.identity=ident;self.records=[];self.pending=None;self.tick=0;self.last_capture=None
        self.reset_id=request['message_id'];self.reset_digest=digest(request)
        self.observation_id=None;self.acks={};self.state='READY'
        self.origin_ns=request['body']['origin_sim_ns'];self.instruction=request['body']['task']['instruction']
        self.sensor_ids={k:None for k in CAMERAS}

    def observe(self, message):
        self._check(message,'Observation');body=message['body']
        require(self.state in ('READY','AWAIT_OBSERVATION'),'state','observation order')
        require(body['tick']==self.tick and body['executed_history']==self.records,'history','unconfirmed history')
        require(body['instruction']==self.instruction,'task','instruction changed')
        first=0 if self.last_capture is None else self.last_capture+40
        expected=list(range(first,self.tick+1,40));seen={k:[] for k in CAMERAS};ids=dict(self.sensor_ids)
        require(expected,'camera','empty observation increment')
        for frame in body['rgb']:
            validate_frame(frame,epoch=self.identity[2],origin_ns=self.origin_ns,last_tick=self.tick)
            k=frame['camera_id'];seen[k].append(frame['capture_tick'])
            require(ids[k] is None or frame['sensor_frame_id']>ids[k],'camera','stale camera frame')
            ids[k]=frame['sensor_frame_id']
        require(all(seen[k]==expected for k in CAMERAS),'timing','camera increments')
        self.sensor_ids=ids;self.last_capture=self.tick;self.observation_id=message['message_id'];self.state='OBSERVED'
        return copy.deepcopy(body)

    def expect_chunk(self, message):
        self._check(message,'ActionChunk');body=message['body']
        require(self.state=='OBSERVED' and self.pending is None,'state','already pending/no observation')
        require(body['observation_id']==self.observation_id and body['start_tick']==self.tick,'timing','chunk origin')
        require(len(body['actions'])>0 and len(body['actions'])%16==0,'action','chunk length')
        self.pending=copy.deepcopy(message);self.state='PENDING'

    def accept_ack(self, message):
        self._check(message,'ExecutionAck');body=message['body'];key=message['message_id'];sha=digest(message)
        if key in self.acks:
            require(self.acks[key]==sha,'duplicate','conflicting acknowledgement')
            return copy.deepcopy(self.records)
        require(self.pending is not None and self.state=='PENDING','state','unsolicited acknowledgement')
        request=self.pending['body'];rows=body['commands']
        require(body['chunk_id']==request['chunk_id'] and body['start_tick']==self.tick and len(rows)==len(request['actions']),'execution','ack request mismatch')
        end=body['end_tick'];require(self.tick<=end<=self.tick+10*len(rows) and (end-self.tick)%5==0,'timing','ack interval')
        for i,row in enumerate(rows):
            validate_command(row)
            require(row['command_id']==f"{body['chunk_id']}:{i}" and row['start_tick']==self.tick+i*10 and row['requested']==request['actions'][i],'execution','ack command mismatch')
            require(row['executed_until_tick']==max(row['start_tick'],min(end,row['end_tick'])),'execution','ack prefix coverage')
        completed=[r for r in rows if r['status']=='completed']
        require(body['completed_count']==len(completed),'execution','ack count')
        require(body['reason']!='completed' or len(completed)==len(rows),'execution','premature completion')
        self.records.extend(copy.deepcopy(completed));self.tick=end;self.pending=None;self.acks[key]=sha
        self.state='AWAIT_OBSERVATION' if len(completed)==len(rows) and body['reason']=='completed' else 'ENDED'
        return copy.deepcopy(self.records)
