from copy import deepcopy
from types import SimpleNamespace
import os
import errno
from pathlib import Path
import pytest
from qlm_bench.backends.mujoco.training_pool import validate,ResetSchedule,TASKS,HORIZONS
from qlm_bench.backends.mujoco.training_live import assert_cpu_runtime


def pool():
    episodes=[{'episode_uid':f'{t}-{i}','task':t,'resource_identity':'scene',
               'initial_state':{'model_identity':'scene'},'horizon_s':HORIZONS[t]} for t in TASKS for i in range(80)]
    return {'schema':'qlm-opd-v4-train-pool-v1','diagnostic_only':False,
      'dataset_revision':'470e0a1f290ef65a25ca1933a91a51ccd6427fcf',
      'payload_revision':'b84488eca8a723767cef27fa455ec2ea8169f81c','tasks':list(TASKS),
      'episodes':episodes,'resources':{'scene':{}},'heldout_uids':['held-out'],
      'releases':[{'train_uids':[r['episode_uid'] for r in episodes],
                   'validation_uids':['held-out'],'test_uids':[]}],
      'runtime':{'backend':'native','controller_device':'cpu','render_backend':'osmesa',
                 'renderer':'llvmpipe','rgb_profile':'dual-rgb-360p-v1'}}


def test_train_pool_disjoint_and_deterministic_ten_task_rotation():
    m=pool();validate(m)
    schedules=[ResetSchedule(m,r,8) for r in range(8)]
    rows=[s.next() for _ in range(2) for s in schedules]
    assert {r['task'] for r in rows}==set(TASKS)
    assert len({r['episode_uid'] for r in rows})==16
    a,b=ResetSchedule(m,0,1),ResetSchedule(m,0,1)
    assert [a.next() for _ in range(800)]==[b.next() for _ in range(800)]
    bad=deepcopy(m);bad['episodes'][0]['episode_uid']='held-out'
    with pytest.raises(ValueError,match='held-out'):validate(bad)
    bad=deepcopy(m);bad['runtime']['render_backend']='egl'
    with pytest.raises(ValueError,match='CPU-only'):validate(bad)


def test_software_rendering_guard(monkeypatch):
    monkeypatch.setenv('MUJOCO_GL','osmesa')
    r=SimpleNamespace(physics=SimpleNamespace(backend='native'),
      core=SimpleNamespace(device='cpu',actor=SimpleNamespace(parameters=lambda:[])),
      renderer=SimpleNamespace(gl_identity={'renderer':'llvmpipe LLVM'}),rgb_profile='dual-rgb-360p-v1')
    assert assert_cpu_runtime(r)['physics']=='native_cpu'
    r.renderer.gl_identity['renderer']='AMD Radeon'
    with pytest.raises(ValueError,match='no GPU fallback'):assert_cpu_runtime(r)
    r.physics.backend='mjwarp'
    with pytest.raises(ValueError,match='Native'):assert_cpu_runtime(r)


def test_feedback_stop_prevents_extra_predict():
    from test_live_inference import Runtime,PhysicalPolicy
    from qlm_bench.live import SynchronousDriver
    policy=PhysicalPolicy()
    class Client:
        calls=[]
        def call(self,method,payload,**identity):
            self.calls.append(method)
            response=policy({'method':method,'payload':payload,**identity})
            if method=='feedback':response={**response,'stop_after_feedback':self.calls.count('feedback')==3}
            return response
    runtime=Runtime();client=Client()
    driver=SynchronousDriver(runtime,client,session_id='train',instruction='Push',max_groups=100)
    driver.reset_episode('episode',policy_seed=42)
    result=driver.run_episode(feedback_hook=lambda response:response['stop_after_feedback'])
    assert result['training_budget_end'] and result['termination_reason']=='training_budget_end'
    assert not result['task_terminal'] and runtime.steps==48
    assert client.calls.count('predict')==3 and runtime.reset_count==1


def test_pool_cannot_relabel_heldout_as_train(tmp_path,monkeypatch):
    import json
    from qlm_bench.backends.mujoco import training_pool as module
    manifest=pool();manifest['files']={};manifest['releases']=[]
    manifest['heldout_uids']=[]
    for name in ('scene.xml','controller.pt','agent.yaml','env.yaml'):
        (tmp_path/name).write_text('fixture resource')
        manifest['files'][name]=module.sha(tmp_path/name)
    manifest['controller']='controller.pt'
    manifest['resources']={'scene':{'entrypoint':'scene.xml','files':{'scene.xml':manifest['files']['scene.xml']}}}
    trace=tmp_path/'trace.json'
    trace.write_text(json.dumps({'scene':{'initial_state':{'model_identity':'scene'},'seed':42}}))
    manifest['files']['trace.json']=module.sha(trace)
    entries=[]
    for task in TASKS:
        rows=[r for r in manifest['episodes'] if r['task']==task]
        for i,row in enumerate(rows):
            row.update(instruction=task,difficulty='clean' if i<16 else 'randomized',
                       snapshot_bundle_sha256='snapshot',source_trace_manifest_sha256=module.sha(trace),
                       source_trace='trace.json',seed=42,goal_overlay={})
        heldout=task+'-test'
        manifest['heldout_uids'].append(heldout)
        source={'split':{'train':[r['episode_uid'] for r in rows],'validation':[],'test':[heldout]},
                'episodes':rows+[dict(rows[0],episode_uid=heldout)]}
        name=task+'.json';(tmp_path/name).write_text(json.dumps(source))
        ref={'manifest_sha256':module.sha(tmp_path/name)}
        manifest['files'][name]=ref['manifest_sha256']
        manifest['releases'].append({'task':task,'ref':ref,'source_manifest':name,
            'train_uids':source['split']['train'],'validation_uids':[],'test_uids':[heldout]})
        entries.append({'task':task,'instruction':task,'ref':ref})
    cat=tmp_path/'catalogue.json';cat.write_text(json.dumps({'demonstrations':entries}))
    monkeypatch.setattr(module,'catalogue',lambda:cat)
    manifest['catalog_sha256']=module.sha(cat)
    path=tmp_path/'manifest.json'
    def write(value):path.write_text(json.dumps(value))
    write(manifest);assert len(module.load(path)['episodes'])==800
    bad=deepcopy(manifest)
    old=bad['episodes'][0]['episode_uid'];new=TASKS[0]+'-test'
    bad['episodes'][0]['episode_uid']=new
    bad['releases'][0]['train_uids'][0]=new
    bad['releases'][0]['test_uids']=[old]
    bad['heldout_uids'][bad['heldout_uids'].index(new)]=old
    # Internally consistent forged labels used to pass validate AND load.
    validate(bad)
    write(bad)
    with pytest.raises(ValueError,match='authenticated source split'):module.load(path)
    bad=deepcopy(manifest);bad['episodes'][0]['difficulty']='randomized';write(bad)
    with pytest.raises(ValueError,match='difficulty changed'):module.load(path)
    bad=deepcopy(manifest);bad['episodes'][0]['seed']=17;write(bad)
    with pytest.raises(ValueError,match='authenticated source trace'):module.load(path)
    bad=deepcopy(manifest);del bad['files']['scene.xml'];write(bad)
    with pytest.raises(ValueError,match='Unbound training resource'):module.load(path)


def test_cpu_worker_environment_is_selected_before_mujoco(monkeypatch):
    import sys
    from qlm_bench.backends.mujoco.training_live import select_cpu_environment,CPU_ENV
    monkeypatch.delitem(sys.modules,'mujoco',raising=False)
    for name in CPU_ENV:monkeypatch.setenv(name,'inherited-gpu-setting')
    select_cpu_environment()
    assert all(os.environ[k]==v for k,v in CPU_ENV.items())
    monkeypatch.setitem(sys.modules,'mujoco',object())
    monkeypatch.setenv('MUJOCO_GL','egl')
    with pytest.raises(RuntimeError,match='before importing MuJoCo'):select_cpu_environment()


@pytest.mark.parametrize("error", [errno.EOPNOTSUPP, errno.EMLINK])
def test_pool_dedup_falls_back_without_hardlink_support(tmp_path,monkeypatch,error):
    from pathlib import Path
    import errno
    from qlm_bench.backends.mujoco.training_pool import copy_duplicate,sha
    source=tmp_path/'source';source.write_bytes(b'unchanged-resource')
    def unsupported(*args,**kwargs):raise OSError(error,'fixture filesystem')
    monkeypatch.setattr(Path,'hardlink_to',unsupported)
    target=tmp_path/'copy';copy_duplicate(source,target)
    assert sha(target)==sha(source) and target.stat().st_ino!=source.stat().st_ino


@pytest.mark.parametrize('error',[errno.ENOSPC,errno.EIO])
def test_pool_dedup_does_not_swallow_storage_failures(tmp_path,monkeypatch,error):
    from qlm_bench.backends.mujoco.training_pool import copy_duplicate
    source=tmp_path/'source';source.write_bytes(b'resource')
    def failed(*args,**kwargs):raise OSError(error,'fixture storage failure')
    monkeypatch.setattr(Path,'hardlink_to',failed)
    with pytest.raises(OSError) as failure:copy_duplicate(source,tmp_path/'target')
    assert failure.value.errno==error and not (tmp_path/'target').exists()


def test_pool_dedup_mixes_hardlinks_and_copies_at_link_max_127(tmp_path,monkeypatch):
    from qlm_bench.backends.mujoco.training_pool import copy_duplicate,sha
    source=tmp_path/'source';source.write_bytes(b'original-resource-bytes')
    hardlink=Path.hardlink_to
    def limited(target,original):
        if Path(original).stat().st_nlink>=127:raise OSError(errno.EMLINK,'fixture LINK_MAX=127')
        return hardlink(target,original)
    monkeypatch.setattr(Path,'hardlink_to',limited)
    targets=[tmp_path/str(i) for i in range(130)]
    for target in targets:copy_duplicate(source,target)
    assert source.stat().st_nlink==127
    assert targets[125].stat().st_ino==source.stat().st_ino
    assert targets[126].stat().st_ino!=source.stat().st_ino
    assert all(sha(target)==sha(source) for target in targets)
