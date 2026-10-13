"""Re-tessellate every original CAD face; no feature deletion or hull substitution."""
import argparse,json,time,hashlib
from pathlib import Path
import numpy as np
from OCP.BRep import BRep_Builder,BRep_Tool
from OCP.BRepTools import BRepTools
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopAbs import TopAbs_ShapeEnum,TopAbs_Orientation
from OCP.TopExp import TopExp_Explorer
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import TopoDS,TopoDS_Shape

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser();p.add_argument('--assembly',required=True);p.add_argument('--output',required=True);p.add_argument('--linear-mm',type=float,default=.35);p.add_argument('--angular-rad',type=float,default=.35)
 a=p.parse_args();ref=Path(a.assembly);out=Path(a.output);out.mkdir(parents=True,exist_ok=False);identity=json.loads((ref/'result.json').read_text());records=[]
 for row in identity['components']:
  if row['name'] not in ('基础框架最终版1-6','单支架'):continue
  source=ref/row['brep'];assert sha(source)==row['brep_sha256'];shape=TopoDS_Shape();assert BRepTools.Read_s(shape,str(source),BRep_Builder())
  BRepTools.Clean_s(shape);start=time.monotonic();mesher=BRepMesh_IncrementalMesh(shape,a.linear_mm,False,a.angular_rad,True)
  if not mesher.IsDone():raise ValueError('LOD meshing failed')
  vertices=[];normals=[];faces=[];source_faces=[];offset=0;missing=[];removed=0;index=0;explorer=TopExp_Explorer(shape,TopAbs_ShapeEnum.TopAbs_FACE)
  while explorer.More():
   face=TopoDS.Face_s(explorer.Current());loc=TopLoc_Location();tri=BRep_Tool.Triangulation_s(face,loc)
   if tri is None or not tri.NbTriangles():missing.append(index);index+=1;explorer.Next();continue
   tri.ComputeNormals();t=loc.Transformation();v=np.asarray([tri.Node(i).Transformed(t).Coord() for i in range(1,tri.NbNodes()+1)]);n=np.asarray([tri.Normal(i).Transformed(t).Coord() for i in range(1,tri.NbNodes()+1)]);f=np.asarray([tri.Triangle(i).Get() for i in range(1,tri.NbTriangles()+1)])-1
   if face.Orientation()==TopAbs_Orientation.TopAbs_REVERSED:f=f[:,[0,2,1]];n=-n
   valid=np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1)>1e-14;removed+=int((~valid).sum());f=f[valid]
   vertices.append(v);normals.append(n);faces.append(f+offset);source_faces.extend([index]*len(f));offset+=len(v);index+=1;explorer.Next()
  if missing:raise ValueError('LOD lost source faces:'+str(missing))
  v=np.concatenate(vertices);n=np.concatenate(normals);f=np.concatenate(faces);path=out/(Path(row['brep']).stem+'.npz');np.savez_compressed(path,vertices_mm=v,normals=n,faces=f,source_face=np.asarray(source_faces))
  r={'name':row['name'],'brep':row['brep'],'mesh':path.name,'vertices':len(v),'triangles':len(f),'source_faces':index,'missing_face_indices':missing,'zero_area_triangles_removed':removed,'bounds_mm':[v.min(0).tolist(),v.max(0).tolist()],'linear_deflection_mm':a.linear_mm,'angular_deflection_rad':a.angular_rad,'mesh_sha256':sha(path),'elapsed_s':time.monotonic()-start};records.append(r);print(r,flush=True)
 report={'passed':True,'work_id':'QLM-SIM-009','source_STEP_sha256':identity['source_sha256'],'components':records,'source_units':'millimetres','method':'all original CAD faces/features retained,uniform bounded coarser tessellation','total_triangles':sum(r['triangles'] for r in records)}
 (out/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
