"""Lossless geometry/material inspection for explicit USD preparation tools.

No simulator or controller is imported here. USD is an asset-preparation dependency,
not a dependency of the public QLM metadata/data/protocol package.
"""
from pathlib import Path
import hashlib
import json
import math

import numpy as np
from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def value(v):
    if isinstance(v,Sdf.AssetPath):return {'asset_path':v.path,'resolved_path':v.resolvedPath}
    if isinstance(v,(Gf.Quatf,Gf.Quatd,Gf.Quath)):
        return {'quaternion_xyzw':[*map(float,v.GetImaginary()),float(v.GetReal())]}
    if isinstance(v,float) and not math.isfinite(v):
        return {'nonfinite_float':'nan' if math.isnan(v) else '+inf' if v>0 else '-inf'}
    if v is None or isinstance(v,(str,int,float,bool)):return v
    if isinstance(v,dict):return {str(k):value(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [value(x) for x in v]
    try:
        a=np.asarray(v)
        if a.dtype.kind=='O' and a.ndim==0:return str(v)
        return value(a.tolist())
    except (TypeError,ValueError):return str(v)


def attributes(prim, prefixes=None):
    result={}
    for attr in prim.GetAttributes():
        name=attr.GetName()
        if prefixes and not name.startswith(prefixes):continue
        result[name]={'value':value(attr.Get()),'authored':attr.HasAuthoredValueOpinion(),
                      'type':str(attr.GetTypeName())}
    return result


def transform(prim,parent,cache):
    # USD uses row-vector matrices. Keep the exact matrix and explicit convention.
    matrix,reset_stack=cache.ComputeRelativeTransform(prim,parent)
    if reset_stack:raise ValueError('Unexpected resetXformStack between geometry and body: '+str(prim.GetPath()))
    return np.asarray(matrix,dtype=np.float64)


def material(stage,prim,materials,purpose=''):
    bound,_=UsdShade.MaterialBindingAPI(prim).ComputeBoundMaterial(purpose)
    if not bound:return None
    key=str(bound.GetPath())
    if key not in materials:
        nodes={}
        for child in Usd.PrimRange(bound.GetPrim()):
            if child.IsA(UsdShade.Shader) or child.IsA(UsdShade.NodeGraph):
                nodes[str(child.GetPath())]={'type':child.GetTypeName(),'attributes':attributes(child),
                    'connections':{a.GetName():[str(x) for x in a.GetConnections()]
                                   for a in child.GetAttributes() if a.GetConnections()}}
        materials[key]={'path':key,'attributes':attributes(bound.GetPrim()),'nodes':nodes}
    return key


def inspect_stage(stage,root_path,output,*,body_paths=None):
    """Export exact USD geometry arrays and body-local transforms; no conversion."""
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    root=stage.GetPrimAtPath(root_path)
    if not root:raise ValueError('Missing USD root '+root_path)
    cache=UsdGeom.XformCache();arrays={};geometries=[];materials={};joints=[]
    body_paths=set(body_paths or [str(p.GetPath()) for p in Usd.PrimRange(root,Usd.TraverseInstanceProxies())
                                  if p.HasAPI(UsdPhysics.RigidBodyAPI)])
    bodies={}
    for path in sorted(body_paths):
        p=stage.GetPrimAtPath(path)
        if not p:raise ValueError('Missing rigid body '+path)
        bodies[path]={'name':p.GetName(),'root_transform_row_major':transform(p,root,cache).tolist(),
                      'attributes':attributes(p,('physics:','physx','xformOp:'))}
    for prim in Usd.PrimRange(root,Usd.TraverseInstanceProxies()):
        if prim.IsA(UsdPhysics.Joint):
            joints.append({'path':str(prim.GetPath()),'name':prim.GetName(),'type':prim.GetTypeName(),
                'attributes':attributes(prim),'relationships':{r.GetName():[str(x) for x in r.GetTargets()] for r in prim.GetRelationships()}})
        if not prim.IsA(UsdGeom.Gprim):continue
        path=str(prim.GetPath());owner=prim
        while owner and str(owner.GetPath()) not in body_paths and owner!=root:owner=owner.GetParent()
        owner_path=str(owner.GetPath()) if owner else root_path
        if owner_path not in body_paths:owner=root;owner_path=root_path
        identifier=f'g{len(geometries):04d}'
        imageable=UsdGeom.Imageable(prim)
        m=transform(prim,owner,cache)
        record={'id':identifier,'path':path,'name':prim.GetName(),'type':prim.GetTypeName(),'body':owner_path,
                'body_transform_row_major':m.tolist(),'root_transform_row_major':transform(prim,root,cache).tolist(),
                'purpose':str(imageable.ComputePurpose()),'visibility':str(imageable.ComputeVisibility()),
                'collision_enabled':bool(prim.HasAPI(UsdPhysics.CollisionAPI) and
                    UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Get() is not False),
                'physics_attributes':attributes(prim,('physics:','physx')),
                'material':material(stage,prim,materials)}
        if record['collision_enabled']:
            record['physics_material']=material(stage,prim,materials,'physics')
        if prim.IsA(UsdGeom.Mesh):
            mesh=UsdGeom.Mesh(prim)
            for label,raw in (('points',mesh.GetPointsAttr().Get()),('face_counts',mesh.GetFaceVertexCountsAttr().Get()),
                              ('face_indices',mesh.GetFaceVertexIndicesAttr().Get()),('normals',mesh.GetNormalsAttr().Get())):
                if raw is not None and len(raw):
                    name=identifier+'_'+label;arrays[name]=np.asarray(raw);record[label]=name
            record['normal_interpolation']=str(mesh.GetNormalsInterpolation())
            record['orientation']=str(mesh.GetOrientationAttr().Get())
            record['subdivision_scheme']=str(mesh.GetSubdivisionSchemeAttr().Get())
            record['primvars']={}
            for pv in UsdGeom.PrimvarsAPI(prim).GetPrimvarsWithAuthoredValues():
                raw=pv.ComputeFlattened()
                if raw is None:continue
                a=np.asarray(raw)
                if a.dtype.kind not in 'biuf':continue
                label=identifier+'_pv_'+pv.GetPrimvarName().replace(':','_')
                arrays[label]=a;record['primvars'][pv.GetPrimvarName()]={'array':label,'interpolation':str(pv.GetInterpolation()),'type':str(pv.GetTypeName())}
            record['material_subsets']=[]
            for subset in UsdGeom.Subset.GetAllGeomSubsets(UsdGeom.Imageable(prim)):
                record['material_subsets'].append({'path':str(subset.GetPath()),'indices':list(map(int,subset.GetIndicesAttr().Get())),
                    'element_type':str(subset.GetElementTypeAttr().Get()),'material':material(stage,subset.GetPrim(),materials)})
        else:
            # Preserve primitive parameters exactly; conversion must explicitly
            # support their type and transform rather than approximating silently.
            record['geometry_attributes']=attributes(prim)
        geometries.append(record)
    np.savez_compressed(output/'geometry.npz',**arrays)
    report={'schema':'qlm-usd-reference-v1','root':root_path,'meters_per_unit':UsdGeom.GetStageMetersPerUnit(stage),
            'up_axis':str(UsdGeom.GetStageUpAxis(stage)),'transform_convention':'row-vector USD; p_body=[p,1] @ M',
            'root_attributes':attributes(root),'root_local_transform_row_major':np.asarray(UsdGeom.Xformable(root).GetLocalTransformation()).tolist(),
            'bodies':bodies,'joints':joints,'geometries':geometries,'materials':materials,
            'geometry_arrays_sha256':digest(output/'geometry.npz'),
            'used_layers':[l.identifier for l in stage.GetUsedLayers()],
            'stage_default_prim':str(stage.GetDefaultPrim().GetPath()),
            'conversion_performed':False,'implementation_sha256':digest(__file__)}
    (output/'reference.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return report
