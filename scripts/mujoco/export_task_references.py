"""Hash-check the three original asset packs and export USD preparation references."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import sys

from pxr import Usd


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--resource-root',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).resolve().parents[2]
    path=Path(__file__).with_name('usd_reference.py')
    spec=importlib.util.spec_from_file_location('task_usd_reference',path);usd=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=usd;spec.loader.exec_module(usd)
    results={}
    for task,asset in (('push_box','cardboard-box-05'),('press_button','industrial-button'),('lift_basket','oasis-basket')):
        manifest_path=root/'src/qlm_bench/assets/manifests'/(asset+'.json')
        manifest=json.loads(manifest_path.read_text());source=Path(a.resource_root)/manifest['cache_subdir']
        checked={}
        for name,record in manifest['files'].items():
            payload=source/name
            if not payload.is_file() or payload.stat().st_size!=record['size_bytes'] or sha(payload)!=record['sha256']:
                raise ValueError('Original source resource identity mismatch: '+str(payload))
            checked[name]=record
        stage=Usd.Stage.Open(str(source/manifest['entrypoint']))
        if not stage:raise ValueError('Cannot open original asset '+asset)
        report=usd.inspect_stage(stage,str(stage.GetDefaultPrim().GetPath()),out/task)
        identity={'task':task,'source_asset_manifest':manifest,'source_manifest_sha256':sha(manifest_path),
            'source_root':str(source.resolve()),'verified_files':checked,'reference_sha256':sha(out/task/'reference.json'),
            'license_status_preserved':manifest['license'],'geometry_count':len(report['geometries']),
            'kind':'original_source_asset_inspection_not_migration_acceptance'}
        (out/task/'identity.json').write_text(json.dumps(identity,indent=2)+'\n');results[task]=identity
        print(task,'original resources verified; geometries',len(report['geometries']),flush=True)
    (out/'result.json').write_text(json.dumps({'work_id':'QLM-SIM-005','status':'completed','tasks':results,
        'source_assets_modified':False,'physics_run':False,'conversion_acceptance':False},indent=2)+'\n')


if __name__=='__main__':main()
