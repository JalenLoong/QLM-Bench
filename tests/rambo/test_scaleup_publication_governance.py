"""Independent QLM commit IDs must not inherit shared-v2 authorization by suffix."""
import importlib.util
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('qlm_publication_governance',ROOT/'scripts/check_governance.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)


def test_qualified_qlm_ids_are_registered_independently():
    shared={'DATA-001','INFRA-001'};independent={'QLM-DATA-001','QLM-INFRA-001'}
    assert not g.commit_title_errors('[DATA-001] Historical work',shared)
    assert not g.commit_title_errors('[QLM-INFRA-001][QLM-DATA-001] Publish scale-up source',shared,independent)
    assert g.commit_title_errors('[QLM-DATA-001] Unregistered QLM work',shared)
    assert g.commit_title_errors('[QLM-DATA-002] Unknown work',shared,independent)
    assert g.commit_title_errors('Publish [QLM-DATA-001] without prefix',shared,independent)


def test_qlm_registry_does_not_rewrite_shared_registry(tmp_path):
    path=tmp_path/'docs/scaleup-v1/work-registry.json';path.parent.mkdir(parents=True)
    value={'namespace':'qlm-scaleup-v1','authority_repository':'QLM-Bench',
           'works':[{'id':'QLM-DATA-001'}]}
    path.write_text(json.dumps(value));assert g.qlm_work_ids(tmp_path)=={'QLM-DATA-001'}
    value['authority_repository']='WAM-Policy';path.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='authority'):g.qlm_work_ids(tmp_path)
    value['authority_repository']='QLM-Bench';value['works'].append({'id':'QLM-DATA-001'});path.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='Work IDs'):g.qlm_work_ids(tmp_path)
