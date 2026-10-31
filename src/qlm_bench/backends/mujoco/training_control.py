"""CPU-only training profile and transactional, episode-level task scheduling.

The SQLite file is an address on node-local scratch. Only the portable logical
snapshot enters learner checkpoints; no simulator/model/RPC runs under its lock.
"""
from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path
import random
import sqlite3

from .training_pool import TASKS, digest, sha, load

DESIGN = 'opd-v4-native1-2-5f-900s-v2'
PROFILE = 'qlm-opd-v4-training-profile-v2'
SNAPSHOT = 'qlm-opd-v4-episode-schedule-v1'
TRAIN_HORIZONS = dict(zip(TASKS, (19.2,24,24,24,40,40,32,32,40,40)))
# v2 schedules nine tasks; the train800 pool and its horizons keep all ten (pool identity unchanged).
TRAINING_TASKS = tuple(t for t in TASKS if t != 'sweep_block_to_zone')


def profile(pool_sha256):
    return {'schema':PROFILE, 'design':DESIGN, 'train_pool_sha256':pool_sha256,
            'training_horizons_s':TRAIN_HORIZONS.copy(), 'training_tasks':list(TRAINING_TASKS), 'seed':42,
            'sampling':'global_confirmed_episode_starts_round_robin', 'max_active_per_task':2,
            'runtime':{'physics':'native_cpu','controller':'rambo_cpu','rendering':'osmesa_llvmpipe'}}


def read_profile(path, pool_sha256):
    value=json.loads(Path(path).read_text())
    if value != profile(pool_sha256):
        raise ValueError('Training profile differs from the accepted design/pool/horizons')
    return value


def prepare_profile(pool_path, output, *, diagnostic=False):
    load(pool_path,allow_diagnostic=diagnostic)
    value=profile(sha(pool_path))
    with Path(output).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    return {'profile_sha256':sha(output),'profile':value}


class EpisodeSchedule:
    def __init__(self,path,profile_value,*,timeout=5.):
        self.path=Path(path);self.profile=profile_value;self.timeout=timeout
        if profile_value!=profile(profile_value.get('train_pool_sha256')):
            raise ValueError('Invalid scheduler profile')
        self.tasks=tuple(profile_value['training_tasks'])
        if not 0 < timeout <= 60:raise ValueError('Bounded SQLite timeout required')

    @classmethod
    def create(cls,path,profile_value,pool,segment):
        obj=cls(path,profile_value)
        if obj.path.exists():raise FileExistsError(obj.path)
        if not segment:raise ValueError('New segment identity required')
        decks={t:sorted(r['episode_uid'] for r in pool['episodes'] if r['task']==t) for t in obj.tasks}
        if any(not uids or len(set(uids))!=len(uids) for uids in decks.values()):
            raise ValueError('Each task needs a unique nonempty reset deck')
        for t,uids in decks.items():random.Random(int(digest(['opd4-reset-v1',42,t]),16)).shuffle(uids)
        state={'schema':SNAPSHOT,'profile_sha256':digest(profile_value),'segment':segment,
               'confirmed':dict.fromkeys(obj.tasks,0),'completed':dict.fromkeys(obj.tasks,0),
               'cursor':0,'decks':decks,'used':{t:[] for t in obj.tasks},
               'cycles':dict.fromkeys(obj.tasks,0),'tickets':{},'stopped':False}
        obj.path.parent.mkdir(parents=True,exist_ok=True)
        # Exclusive creation prevents concurrent attempts sharing an existing ledger.
        with obj.path.open('xb'):pass
        with sqlite3.connect(obj.path,timeout=obj.timeout) as db:
            db.execute('CREATE TABLE schedule (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL)')
            db.execute('INSERT INTO schedule VALUES (1,?)',(json.dumps(state,allow_nan=False),))
        return obj

    @contextmanager
    def transaction(self):
        if not self.path.is_file():raise ValueError('Initialize the shared episode schedule before workers')
        db=sqlite3.connect(self.path,timeout=self.timeout,isolation_level=None)
        try:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT payload FROM schedule WHERE id=1').fetchone()
            state=json.loads(row[0]);self.validate(state)
            yield state
            self.validate(state)
            db.execute('UPDATE schedule SET payload=? WHERE id=1',(json.dumps(state,allow_nan=False),))
            db.execute('COMMIT')
        except BaseException:
            if db.in_transaction:db.execute('ROLLBACK')
            raise
        finally:db.close()

    def validate(self,s):
        if s.get('schema')!=SNAPSHOT or s.get('profile_sha256')!=digest(self.profile):
            raise ValueError('Schedule schema/profile identity mismatch')
        if not isinstance(s.get('segment'),str) or not s['segment'] or type(s.get('stopped')) is not bool:
            raise ValueError('Invalid segment/stop state')
        tasks=self.tasks
        if type(s.get('cursor')) is not int or not 0<=s['cursor']<len(tasks):raise ValueError('Invalid round-robin cursor')
        if set(s['decks'])!=set(tasks) or set(s['used'])!=set(tasks):raise ValueError('Invalid scheduled task set')
        for field in ('confirmed','completed','cycles'):
            if set(s[field])!=set(tasks) or any(type(v) is not int or v<0 for v in s[field].values()):
                raise ValueError('Invalid task counters')
        for t in tasks:
            if len(set(s['decks'][t]))!=len(s['decks'][t]) or not s['decks'][t]:raise ValueError('Invalid reset deck')
            if len(set(s['used'][t]))!=len(s['used'][t]) or not set(s['used'][t])<=set(s['decks'][t]):raise ValueError('Invalid consumed reset deck')
            if s['completed'][t]>s['confirmed'][t]:raise ValueError('Invalid completion count')
        active={t:[] for t in tasks}
        for key,v in s['tickets'].items():
            if v['task'] not in tasks or v['episode_uid'] not in s['decks'][v['task']]:raise ValueError('Unbound ticket reset')
            if v['status'] not in ('reserved','active','finished','cancelled','interrupted'):raise ValueError('Invalid ticket status')
            if v['status'] in ('reserved','active'):active[v['task']].append(v['episode_uid'])
        for t in tasks:
            if s['confirmed'][t]!=sum(v['task']==t and v['status'] in ('active','finished','interrupted') for v in s['tickets'].values()):raise ValueError('Confirmed count/ticket mismatch')
            if s['completed'][t]!=sum(v['task']==t and v['status']=='finished' for v in s['tickets'].values()):raise ValueError('Completion count/ticket mismatch')
            if s['confirmed'][t]!=80*s['cycles'][t]+len(s['used'][t]) and len(s['decks'][t])==80:raise ValueError('Consumed deck/count mismatch')
        if any(len(x)>2 or len(x)!=len(set(x)) for x in active.values()):raise ValueError('Episode concurrency/reservation violation')

    def reserve(self,segment,stream,episode_index):
        if type(stream) is not int or stream<0 or type(episode_index) is not int or episode_index<0:
            raise ValueError('Nonnegative stream/episode identity required')
        key=json.dumps([segment,stream,episode_index],separators=(',',':'))
        with self.transaction() as s:
            if segment!=s['segment']:raise ValueError('Stale schedule segment')
            if key in s['tickets']:return deepcopy(s['tickets'][key])
            if s['stopped']:raise ValueError('Training stopped; no new episode tickets')
            if any(v['segment']==segment and v['stream']==stream and v['status'] in ('reserved','active') for v in s['tickets'].values()):
                raise ValueError('Stream still owns an episode reservation')
            tasks=self.tasks
            active={t:[v['episode_uid'] for v in s['tickets'].values() if v['task']==t and v['status'] in ('reserved','active')] for t in tasks}
            # A task below the concurrency cap can still have its final unused
            # reset reserved by another worker. Do not abort while other tasks
            # have available candidates, or consume a reservation prematurely.
            candidates={}
            for t in tasks:
                used=[] if len(s['used'][t])==len(s['decks'][t]) else s['used'][t]
                candidates[t]=[uid for uid in s['decks'][t] if uid not in used and uid not in active[t]]
            eligible=[t for t in tasks if len(active[t])<2 and candidates[t]]
            if not eligible:raise RuntimeError('No eligible episode slot')
            order=tasks[s['cursor']:]+tasks[:s['cursor']]
            task=min(eligible,key=lambda t:(s['confirmed'][t],order.index(t)))
            if len(s['used'][task])==len(s['decks'][task]):
                s['used'][task]=[];s['cycles'][task]+=1
            ticket={'id':key,'segment':segment,'stream':stream,'episode_index':episode_index,'task':task,
                    'episode_uid':candidates[task][0],'cycle':s['cycles'][task],'status':'reserved'}
            s['tickets'][key]=ticket;s['cursor']=(tasks.index(task)+1)%len(tasks)
            return deepcopy(ticket)

    def confirm(self,ticket_id):
        with self.transaction() as s:
            v=s['tickets'][ticket_id]
            if v['status'] in ('active','finished'):return deepcopy(v)
            if v['status']!='reserved' or s['stopped']:raise ValueError('Cannot confirm retired/stopped ticket')
            s['confirmed'][v['task']]+=1;s['used'][v['task']].append(v['episode_uid']);v['status']='active'
            return deepcopy(v)

    def finish(self,ticket_id,*,natural):
        with self.transaction() as s:
            v=s['tickets'][ticket_id]
            if v['status'] in ('finished','interrupted'):return
            if v['status']!='active':raise ValueError('Finish requires a confirmed start')
            if natural:s['completed'][v['task']]+=1
            v['status']='finished' if natural else 'interrupted'

    def cancel(self,ticket_id):
        with self.transaction() as s:
            v=s['tickets'][ticket_id]
            if v['status']=='reserved':v['status']='cancelled'
            elif v['status']=='active':v['status']='interrupted'

    def snapshot(self):
        with self.transaction() as s:return deepcopy(s)

    def restore(self,snapshot,segment):
        self.validate(snapshot)
        with self.transaction() as s:
            if s['tickets'] or any(s['confirmed'].values()):raise ValueError('Restore only into a new empty schedule')
            if snapshot['decks']!=s['decks']:raise ValueError('Reset candidate decks changed')
            recovered=deepcopy(snapshot);recovered['segment']=segment;recovered['stopped']=False
            for v in recovered['tickets'].values():
                if v['status']=='reserved':v['status']='cancelled'
                elif v['status']=='active':v['status']='interrupted'
            s.clear();s.update(recovered)

    def stop(self):
        with self.transaction() as s:s['stopped']=True
