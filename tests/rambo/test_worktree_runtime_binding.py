"""The fixed interpreter executes this worktree, even with an old editable checkout."""
from pathlib import Path
import json
import os
import subprocess


def test_runtime_wrapper_replaces_caller_source_paths_without_reinstall():
    root=Path(__file__).resolve().parents[2]
    venv=os.environ.get('RAMBO_VENV')
    if venv is None:
        venv=str(root.parents[1]/'envs/rambo-isaac60-py312')
    code="""from pathlib import Path
import rambo,crl2,json,sys
from rambo.tasks.common.environment_factory import TASK_IDS
from rambo.tasks.common.episode import EpisodeRuntime
assert 'isaaclab' not in sys.modules and 'omni.kit.app' not in sys.modules
print(json.dumps({'rambo':str(Path(rambo.__file__).resolve()),'crl2':str(Path(crl2.__file__).resolve()),'tasks':list(TASK_IDS)}))
"""
    env=dict(os.environ,RAMBO_VENV=venv,PYTHONPATH='/tmp/nonexistent-old-checkout')
    run=subprocess.run([str(root/'scripts/rambo/run.sh'),'-c',code],env=env,cwd='/tmp',text=True,capture_output=True)
    assert run.returncode==0,run.stderr
    data=json.loads(run.stdout)
    assert Path(data['rambo']).is_relative_to(root/'source/rambo')
    assert Path(data['crl2']).is_relative_to(root/'source/crl2')
    assert len(data['tasks'])==3
