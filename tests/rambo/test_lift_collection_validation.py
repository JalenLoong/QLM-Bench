import json
import pytest
from rambo.dataset_v2.validation import _task_contact_diagnostics,file_hash
from rambo.contracts_v2.validation import ContractError

def test_lift_unknown_contact_is_checked(tmp_path):
    path=tmp_path/'contact.json'
    rows=[dict(simulation_time_ns=t,status='unknown',valid=False,fl_object=None,body_object=None,reason='No reliable pair sensor') for t in [0,20000000]]
    data=dict(role='diagnostic_only',unavailable='unknown',bool_columns_are_invalid_placeholders=True,rows=rows)
    path.write_text(json.dumps(data));manifest={'extensions':{'task_profile_version':'lift-basket-v2-2','contact_diagnostics':{'path':'contact.json','sha256':file_hash(path)}}}
    _task_contact_diagnostics(tmp_path,manifest,1)
    rows[1]['fl_object']=False;path.write_text(json.dumps(data));manifest['extensions']['contact_diagnostics']['sha256']=file_hash(path)
    with pytest.raises(ContractError):_task_contact_diagnostics(tmp_path,manifest,1)
