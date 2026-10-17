"""Exact human-approved wording and immutable historical scene compatibility."""
import copy
import pytest
from qlm_bench.tasks.registration import load_registration
from qlm_bench.tasks.prompts import current_instruction_profile

EXPECTED={
 'push_box':'Push the box inside the outlined area.',
 'press_button':'Press the button.',
 'lift_basket':'Lift the basket by its handle.',
 'kick_ball_to_goal':'Kick the ball through the goal.',
 'sweep_block_to_zone':'Sweep the block into the outlined area.',
 'close_fridge_door':'Push against the fridge door until the door closes.',
 'close_oven_door':'Push the oven door until the door closes.',
 'turn_valve':'Rotate the valve lever upward to the upright position.',
 'pull_open_drawer':'Slide your foot into the drawer handle opening and pull the drawer outward.',
 'open_room_door':'Press down the lever handle, then push the door open.',
}
@pytest.mark.parametrize('task',EXPECTED)
def test_exact_current_and_declared_historical_profile(task):
 r=load_registration(task);assert r['instruction']==EXPECTED[task]
 previous=r.get('previous_instructions',[r['instruction']])[0]
 profile=dict(task_id=task,instruction=previous,source_profile=dict(task_text=previous,goal_x=[.1,.2]),success_hold_commands=3,fixture=dict(mass=1.,friction=[.4,.1,.01]))
 original=copy.deepcopy(profile);current=current_instruction_profile(profile)
 assert profile==original and current['instruction']==EXPECTED[task]
 assert current['source_profile']==dict(task_text=EXPECTED[task],goal_x=[.1,.2])
 assert current['fixture']==original['fixture'] and current['success_hold_commands']==3
 if previous!=EXPECTED[task]:assert current['source_instruction']==previous
@pytest.mark.parametrize('task',EXPECTED)
def test_unrecognized_language_is_not_silently_relabelled(task):
 with pytest.raises(ValueError):current_instruction_profile(dict(task_id=task,instruction='Do an unrelated task.'))

@pytest.mark.parametrize('task',[t for t in EXPECTED if t!='kick_ball_to_goal'])
def test_public_profile_load_is_language_only_and_keeps_source_file(tmp_path,task):
    import json
    from qlm_bench.backends.factory import load_model_profile
    r=load_registration(task);old=r.get('previous_instructions',[r['instruction']])[0]
    profile=dict(task_id=task,instruction=old,schema='qlm-mujoco-original-task-v1' if task in ('push_box','press_button','lift_basket') else 'qlm-mujoco-task-candidate-v1',success_hold_commands=3,fixture_mass_kg=1.)
    model=tmp_path/'scene.xml';model.write_text('<mujoco/>');source=model.with_suffix('.task.json');source.write_text(json.dumps(profile));before=source.read_bytes()
    current=load_model_profile(model,task_id=task)
    assert current['instruction']==EXPECTED[task] and current['fixture_mass_kg']==1. and current['success_hold_commands']==3
    assert source.read_bytes()==before
