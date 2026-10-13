"""Tessellate located STEP BReps in millimetres, preserving actual face geometry."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from OCP.BRep import BRep_Builder, BRep_Tool
from OCP.BRepTools import BRepTools
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopAbs import TopAbs_ShapeEnum, TopAbs_Orientation
from OCP.TopExp import TopExp_Explorer
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import TopoDS, TopoDS_Shape


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--assembly',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();ref=Path(a.assembly);out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    identity=json.loads((ref/'result.json').read_text());records=[]
    for row in identity['components']:
        if 'brep' not in row:continue
        name=row['name'];source=ref/row['brep'];shape=TopoDS_Shape()
        if sha(source)!=row['brep_sha256']:raise ValueError('BRep identity changed')
        print('Reading',name,flush=True)
        if not BRepTools.Read_s(shape,str(source),BRep_Builder()):raise ValueError('BRep read failed')
        # Original precise CAD surfaces -> triangles; no decimation or hull replacement.
        deflection=.20 if name!='go2机器狗' else .8
        start=time.monotonic();mesher=BRepMesh_IncrementalMesh(shape,deflection,False,.15,True)
        print('Meshing',name,'done',mesher.IsDone(),flush=True)
        vertices=[];normals=[];faces=[];face_index=[];missing=[];degenerate=0;offset=0
        explorer=TopExp_Explorer(shape,TopAbs_ShapeEnum.TopAbs_FACE);index=0
        while explorer.More():
            face=TopoDS.Face_s(explorer.Current());loc=TopLoc_Location();tri=BRep_Tool.Triangulation_s(face,loc)
            if tri is None or tri.NbTriangles()==0:
                missing.append(index);index+=1;explorer.Next();continue
            tri.ComputeNormals();transform=loc.Transformation()
            xyz=np.asarray([tri.Node(i).Transformed(transform).Coord() for i in range(1,tri.NbNodes()+1)],float)
            n=np.asarray([tri.Normal(i).Transformed(transform).Coord() for i in range(1,tri.NbNodes()+1)],float)
            triangles=np.asarray([tri.Triangle(i).Get() for i in range(1,tri.NbTriangles()+1)],int)-1
            if face.Orientation()==TopAbs_Orientation.TopAbs_REVERSED:
                triangles=triangles[:,[0,2,1]];n=-n
            valid=np.linalg.norm(np.cross(xyz[triangles[:,1]]-xyz[triangles[:,0]],xyz[triangles[:,2]]-xyz[triangles[:,0]]),axis=1)>1e-14
            degenerate+=int((~valid).sum());triangles=triangles[valid]
            vertices.append(xyz);normals.append(n);faces.append(triangles+offset)
            face_index.extend([index]*len(triangles));offset+=len(xyz)
            index+=1;explorer.Next()
        if not vertices:raise ValueError('No finite mesh for '+name)
        vertices=np.concatenate(vertices);normals=np.concatenate(normals);faces=np.concatenate(faces)
        if not np.isfinite(vertices).all() or np.max(np.abs(vertices))>1e6:raise ValueError('Unbounded/nonfinite CAD triangulation')
        stem=Path(row['brep']).stem
        np.savez_compressed(out/(stem+'.npz'),vertices_mm=vertices,normals=normals,faces=faces,source_face=np.asarray(face_index))
        bounds=np.stack([vertices.min(0),vertices.max(0)])
        record={'name':name,'brep':row['brep'],'mesh':stem+'.npz','vertices':len(vertices),'triangles':len(faces),
                'source_faces':index,'missing_face_indices':missing,'zero_area_triangles_removed':degenerate,
                'bounds_mm':bounds.tolist(),'linear_deflection_mm':deflection,'angular_deflection_rad':.15,
                'mesh_sha256':sha(out/(stem+'.npz')),'elapsed_s':time.monotonic()-start}
        records.append(record);print('Mesh',record,flush=True)
        # Selected support/frame must be completely triangulated; robot is only a registration reference.
        if name!='go2机器狗' and missing:raise ValueError('Support CAD faces lack triangulation; cannot silently omit')
    report={'passed':True,'source_STEP_sha256':identity['source_sha256'],'components':records,'source_units':'millimetres'}
    (out/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
