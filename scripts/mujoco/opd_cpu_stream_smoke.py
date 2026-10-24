"""At most six real CPU chunks with a constant mock policy; zero WAM inference."""
import argparse
import json
from pathlib import Path
import threading
import time


def main():
    p=argparse.ArgumentParser();p.add_argument('--pool',required=True);p.add_argument('--output',required=True)
    a=p.parse_args()
    from qlm_bench.backends.mujoco.training_live import select_cpu_environment,run_worker
    select_cpu_environment()
    from qlm_bench.backends.mujoco.training_pool import sha
    from qlm_bench.live import RPCServer,PolicyHistory,make_message
    class Mock:
        def __init__(self):
            self.history=PolicyHistory();self.chunks=self.updates=self.resets=0;self.prefixes=[]
        def __call__(self,request):
            method,payload=request['method'],request['payload']
            if method=='reset':
                self.resets+=1;self.history.reset(payload['reset']);self.history.observe(payload['observation']['observation'])
                return {'status':'OBSERVED'}
            if method=='predict':
                self.prefixes.append((self.updates,self.history.tick))
                chunk=make_message('ActionChunk',{'observation_id':self.history.observation_id,
                    'chunk_id':f'chunk:{self.history.tick}','start_tick':self.history.tick,'action_period_ticks':10,
                    'actions':[[0.,0.,0.,.1934,.142,.05,0.,0.,0.]]*16},
                    session_id=request['session_id'],episode_id=request['episode_id'],reset_epoch=request['reset_epoch'],
                    message_id=f'action:{self.history.tick}')
                self.history.expect_chunk(chunk);return chunk
            if method=='feedback':
                self.history.accept_ack(payload['ack'])
                if payload['observation'] is not None:self.history.observe(payload['observation']['observation'])
                self.chunks+=1
                if self.chunks%3==0:
                    time.sleep(.03)  # Real runtime freeze checks bracket this mock learner wait.
                    self.updates+=1
                return {'status':self.history.state,'stop_after_feedback':self.updates==2,
                        'training':{'student_version':self.updates,'stop_reason':'smoke_budget_end'}}
            return {'status':'ENDED'}
    from qlm_bench.backends.mujoco.training_control import prepare_profile,read_profile,EpisodeSchedule
    from qlm_bench.backends.mujoco.training_pool import load
    control=Path(a.output).with_name(Path(a.output).name+'-control');control.mkdir(parents=True,exist_ok=False)
    profile_path=control/'profile.json';prepare_profile(a.pool,profile_path,diagnostic=True)
    EpisodeSchedule.create(control/'schedule.sqlite',read_profile(profile_path,sha(a.pool)),load(a.pool,allow_diagnostic=True),'cpu-smoke')
    mock=Mock();server=RPCServer(mock,port=0,timeout_s=60)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        result=run_worker(a.pool,sha(a.pool),rank=0,world_size=1,port=server.address[1],output=a.output,
                          rpc_timeout_s=60,wall_timeout_s=580,max_episodes=6,allow_diagnostic=True,segment='cpu-smoke',
                          training_profile=profile_path,schedule_db=control/'schedule.sqlite')
        if mock.chunks!=6 or mock.updates!=2 or mock.resets!=1:
            raise RuntimeError('Expected one episode across two mock updates and exactly six chunks')
        if mock.prefixes!=[(i//3,i*160) for i in range(6)]:raise RuntimeError('Mock updates reset or skipped physical history')
        report={'passed':True,'evidence':'actual_cpu_environment_mock_policy','physical_chunks':6,
                'mock_updates':2,'real_model_optimizer_updates':0,'policy_inference_calls':0,
                'resets':mock.resets,'prefixes':mock.prefixes,'worker':result}
        (Path(a.output)/'mock-stream-result.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report))
    finally:server.shutdown();server.close();thread.join(timeout=5)


if __name__=='__main__':main()
