"""Current task wording over immutable historical scene profiles."""
import copy
from .registration import load_registration, SCALEUP_TASK_IDS

def current_instruction_profile(profile):
    result=copy.deepcopy(profile)
    task=result.get('task_id')
    if task not in SCALEUP_TASK_IDS:
        return result
    registration=load_registration(task)
    current=registration['instruction'];old=result.get('instruction')
    if old not in [current,*registration.get('previous_instructions',[])]:
        raise ValueError('Model profile instruction is not a declared current/historical task prompt')
    if old!=current:
        result['source_instruction']=old
        result['instruction']=current
        result['instruction_revision']=registration['instruction_revision']
        source=result.get('source_profile')
        if isinstance(source,dict):
            for key in ('task_text','instruction'):
                if source.get(key)==old:source[key]=current
    return result
