"""Public EvalCase/EvaluationRunner integration for explicit MuJoCo engineering cases."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import shutil

from qlm_bench.backends.controller import ControllerRuntimeAdapter
from qlm_bench.backends.factory import create_runtime,load_model_profile
from qlm_bench.evaluation import EvalCase,EvaluationProtocol,EvaluationRunner,TrialSpec,write_result
from qlm_bench.policy_interface import ObservationProfile,Native9Command
from qlm_bench.policy_interface.physical import CAMERAS,ROOT_FIELDS
from .defaults import add_model_arguments,resolve_model,validate_default_identity

CONTROLLER='rambo-original-model2000-case-rng-v1'


def prepare_bundle(model,backend,seed,commands,case_id):
    from .physics import MuJoCoPhysics
    from .resources import resource_closure
    profile=load_model_profile(model);resources=resource_closure(model,require_portable=True)
    validate_default_identity(model,resources)
    physics=MuJoCoPhysics(model,backend='native',device='cpu');snapshot=physics.snapshot();physics.close()
    semantics=dict(reference='root_link',quaternion='xyzw',velocity_frame='world',projected_gravity_frame='body',
                   ground_z=0.,ground_reference='push-box-v2-plane-world-z0')
    observation=ObservationProfile('qlm-measured-root-link-dual-rgb-v1',CAMERAS,ROOT_FIELDS,True,semantics)
    frozen=json.loads((Path(__file__).resolve().parents[2]/'compatibility/dataset_v2/spec/profile.json').read_text())
    runtime_profile='mujoco-'+backend+'-original-v1'
    case=EvalCase(case_id,profile['task_id'],profile['asset_profile'],profile['instruction'],observation,
        {profile['asset_id']:resources['identity']},
        {'qpos':snapshot['qpos'].tolist(),'qvel':snapshot['qvel'].tolist(),'simulation_time_ns':0},
        {'position':profile['canonical_goal_position'],'task_profile':profile['asset_profile']},
        {'resource_identity':resources['identity'],'horizon_s':commands*.02},
        frozen['policy_camera_geometry'],seed,CONTROLLER,runtime_profile,
        {'kind':'compiled_original_profile','physics_steps_during_reset':0,'clear_controller_history':True},
        {'evidence_kind':'prepared_engineering_fixture','resource_identity':resources['identity'],
         'preparation_note':'Actual reconstruction is checked by adapter.reset; preparation is not benchmark admission'},
        'engineering_fixture')
    repo=Path(__file__).resolve().parents[4]
    commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    protocol=EvaluationProtocol('mujoco-engineering-v1','original-three-task-engineering','declared-local-case',runtime_profile,
        CONTROLLER,commands,'count_as_failure','first_attempt','engineering_diagnostic','draft',
        (TrialSpec(case_id+'-trial-1',case_id,profile['task_id'],seed),),
        {'source_commit':commit,'spec_sha256':hashlib.sha256(json.dumps(case.record(),sort_keys=True).encode()).hexdigest()})
    return {'schema':'qlm-mujoco-engineering-evaluation-v1','cases':[case.record()],'protocol':protocol.record()}


class MuJoCoEvaluationAdapter(ControllerRuntimeAdapter):
    def __init__(self,runtime,*,output,ffmpeg,ffprobe):
        from qlm_bench.live.media import ActualRGBRecorder
        self.output=Path(output);self.output.mkdir(parents=True,exist_ok=False)
        self.media=ActualRGBRecorder(self.output/'actual_media',ffmpeg=ffmpeg,ffprobe=ffprobe,
            identity={'kind':'public_evaluation_actual_media','resources':runtime.physics.resource_profile,'profile':runtime.profile})
        runtime.on_observation=self.media.observe;runtime.on_terminal=self.media.seal_terminal
        super().__init__(runtime,reconstruct=self.reconstruct_case)

    def reconstruct_case(self,runtime,case):
        import numpy as np
        resource=runtime.physics.model_identity;p=runtime.profile
        expected_runtime='mujoco-'+runtime.physics.backend+'-original-v1'
        if case.task_id!=p['task_id'] or case.instruction!=p['instruction'] or case.runtime_profile!=expected_runtime or case.controller_profile!=CONTROLLER:
            raise ValueError('Case task/runtime/controller differs from the selected backend')
        if dict(case.assets)!={p['asset_id']:resource} or case.scene.get('resource_identity')!=resource:
            raise ValueError('Case asset identity differs; nominal reset cannot replace another case')
        if case.goal!={'position':p['canonical_goal_position'],'task_profile':p['asset_profile']}:
            raise ValueError('Case goal differs from immutable task profile')
        frozen=json.loads((Path(__file__).resolve().parents[2]/'compatibility/dataset_v2/spec/profile.json').read_text())
        if dict(case.cameras)!=frozen['policy_camera_geometry'] or case.reset_procedure.get('kind')!='compiled_original_profile':
            raise ValueError('Unimplemented camera/reset reconstruction requested')
        if case.initial_state.get('simulation_time_ns')!=0:
            raise ValueError('Evaluation reconstruction requires a zero-time initial state')
        initial={'schema':'qlm-mujoco-initial-state-v1','model_identity':resource,
                 'qpos':case.initial_state['qpos'],'qvel':case.initial_state['qvel']}
        runtime.set_case_seed(case.seed);runtime.reset(initial_state=initial);snapshot=runtime.physics.snapshot()
        for field in ('qpos','qvel'):
            np.testing.assert_allclose(snapshot[field],case.initial_state[field],rtol=0,atol=1e-6,
                                       err_msg='Case initial state was not reconstructed: '+field)
        if snapshot['physics_step']!=0 or snapshot['simulation_time_ns']!=case.initial_state['simulation_time_ns']:
            raise ValueError('Case reset clock mismatch')
        self._write(self.output/'reconstruction.json',{'passed':True,'case_id':case.case_id,'case_seed':case.seed,
            'reset_epoch':snapshot['reset_epoch'],'physics_steps_during_reset':0,'resource_identity':resource,
            'RNG':runtime.core.case_rng.identity(),'qpos':snapshot['qpos'].tolist(),'qvel':snapshot['qvel'].tolist()})

    @staticmethod
    def _write(path,value):Path(path).write_text(json.dumps(value,indent=2)+'\n')

    def close(self):
        try:self.media.close()
        finally:super().close()


def run_bundle(bundle,model,checkpoint,backend,out,ffmpeg,ffprobe,provider,expert_profile=None):
    if bundle.get('schema')!='qlm-mujoco-engineering-evaluation-v1':raise ValueError('Explicit engineering evaluation bundle required')
    values=dict(bundle['protocol']);values['expected_trials']=tuple(TrialSpec(**r) for r in values['expected_trials'])
    protocol=EvaluationProtocol(**values)
    if protocol.scope!='engineering_diagnostic' or protocol.max_commands>1200:
        raise ValueError('This entry is bounded P0-P2 engineering, not formal benchmark admission')
    cases={c['case_id']:EvalCase.from_record(c) for c in bundle['cases']}
    out=Path(out);out.mkdir(parents=True,exist_ok=False);active={};counter=0
    from qlm_bench.collection.orchestrator import source_identity
    repo=Path(__file__).resolve().parents[4];source=source_identity(repo);files={}
    for path in sorted(p for p in (repo/'src/qlm_bench').rglob('*') if p.suffix in ('.py','.json')):
        relative=str(path.relative_to(repo));dest=out/'source_snapshot'/relative;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,dest);files[relative]=hashlib.sha256(path.read_bytes()).hexdigest()
    MuJoCoEvaluationAdapter._write(out/'source_snapshot/identity.json',{'source':source,'files':files})
    def runtime_factory(case):
        nonlocal counter
        counter+=1
        r=create_runtime(case.task_id,backend,model_path=model,checkpoint=checkpoint,
                         device='cpu' if backend=='native' else 'cuda:0',seed=case.seed)
        if abs(case.scene['horizon_s']-protocol.max_commands*.02)>1e-9:raise ValueError('Case/protocol horizon mismatch')
        r.profile['horizon_s']=case.scene['horizon_s']
        adapter=MuJoCoEvaluationAdapter(r,output=out/f'trial_{counter:04d}',ffmpeg=ffmpeg,ffprobe=ffprobe)
        active['runtime']=r
        return adapter
    class Provider:
        def reset(self,context):
            self.context=context;self.counter=0;self.expert=None
            if provider=='expert':
                from .expert_adapter import ExpertAdapter
                r=active['runtime'];self.expert=ExpertAdapter(r.physics,r.core,r.task)
                if expert_profile:self.expert.apply_profile_override(expert_profile)
        def command(self,observation):
            values=self.expert.command()[0] if self.expert else [0.,0.,0.,.1934,.142,.05,0.,0.,0.]
            command=Native9Command.from_values(values,episode_uid=self.context.episode_uid,reset_epoch=self.context.reset_epoch,
                                               command_id='public-eval-'+str(self.counter))
            self.counter+=1;return command
    identity={'kind':'privileged_scripted_expert' if provider=='expert' else 'fixed_stand_provider',
              'code':provider+':sha256:'+hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'adapter':'qlm_bench.backends.controller.ControllerRuntimeAdapter',
              'observation_profile':next(iter(cases.values())).observation_profile.profile_id,
              'expert_override':expert_profile,'model_training':False,'actual_source':source,'implementation':files}
    runner=EvaluationRunner(protocol,cases,runtime_factory=runtime_factory,provider_factory=lambda trial:Provider(),
        source_commit=protocol.source_identity['source_commit'],policy_identity=identity,evidence_kind='actual_runtime')
    try:
        result=runner.run(submission_id='mujoco-public-engineering')
        write_result(out/'result',result['run_manifest'],result['outcomes'])
        MuJoCoEvaluationAdapter._write(out/'result.json',result)
    except BaseException as error:
        MuJoCoEvaluationAdapter._write(out/'failure.json',{'passed':False,'stage':'evaluation_or_result_validation',
            'error':repr(error),'source':source,'actual_trial_evidence_retained':True})
        raise
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('prepare','run'))
    p.add_argument('--backend',choices=('native','mjwarp'),required=True);add_model_arguments(p)
    p.add_argument('--output',required=True);p.add_argument('--seed',type=int,default=42);p.add_argument('--commands',type=int,default=16)
    p.add_argument('--case-id',default='original-case-1');p.add_argument('--config');p.add_argument('--checkpoint')
    p.add_argument('--ffmpeg');p.add_argument('--ffprobe');p.add_argument('--provider',choices=('expert','stand'),default='stand')
    p.add_argument('--expert-profile');p.add_argument('--render-backend',choices=('osmesa','egl'),default='osmesa');a=p.parse_args(argv)
    os.environ['MUJOCO_GL']=a.render_backend if a.mode=='run' else 'disable'
    if not 1<=a.commands<=1200:raise ValueError('Engineering case command bound')
    if a.mode=='prepare':
        a.model=str(resolve_model(a.model,task_id=a.task,model_root=a.model_root))
        load_model_profile(a.model,task_id=a.task)
        out=Path(a.output)
        if out.exists():raise FileExistsError(out)
        out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(prepare_bundle(a.model,a.backend,a.seed,a.commands,a.case_id),indent=2)+'\n')
    else:
        if not all((a.config,a.checkpoint,a.ffmpeg,a.ffprobe)):p.error('run requires config, checkpoint, ffmpeg and ffprobe')
        bundle=json.loads(Path(a.config).read_text())
        tasks={case['task_id'] for case in bundle['cases']}
        if len(tasks)!=1:p.error('A model resource must serve exactly one task per evaluation bundle')
        task=tasks.pop()
        if a.task is not None and a.task!=task:p.error('Declared task differs from evaluation cases')
        a.model=str(resolve_model(a.model,task_id=task,model_root=a.model_root))
        from .resources import resource_closure
        resources=resource_closure(a.model,require_portable=True)
        validate_default_identity(a.model,resources)
        load_model_profile(a.model,task_id=task)
        if any(case['scene']['resource_identity']!=resources['identity'] for case in bundle['cases']):
            raise ValueError('Case resource differs from selected model; replay with explicit original --model or prepare a new LOD case')
        result=run_bundle(bundle,a.model,a.checkpoint,a.backend,a.output,a.ffmpeg,a.ffprobe,
                          a.provider,json.loads(Path(a.expert_profile).read_text()) if a.expert_profile else None)
        if any(r['outcome'] in ('error','not_run') for r in result['outcomes']):raise SystemExit(1)


if __name__=='__main__':main()
