"""Restore exact master tessellation on selected camera-near CAD faces."""
import argparse,json,hashlib,copy
from pathlib import Path
import numpy as np

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser();p.add_argument('--coarse',required=True);p.add_argument('--master',required=True);p.add_argument('--selection',required=True);p.add_argument('--output',required=True)
 a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False);coarse=Path(a.coarse);master=Path(a.master);select=json.loads(Path(a.selection).read_text());ids=set(select['selected_faces']);report=json.loads((coarse/'result.json').read_text());records=[]
 for row in report['components']:
  c=np.load(coarse/row['mesh']);m=np.load(master/row['mesh']);chosen=ids if row['name']=='单支架' else set();vertices=[];normals=[];faces=[];source=[];offset=0
  for i in range(row['source_faces']):
   z=m if i in chosen else c;f=z['faces'][z['source_face']==i]
   if not len(f):continue
   used,local=np.unique(f.reshape(-1),return_inverse=True);vertices.append(z['vertices_mm'][used]);normals.append(z['normals'][used]);faces.append(local.reshape(-1,3)+offset);source.extend([i]*len(f));offset+=len(used)
  v=np.concatenate(vertices);n=np.concatenate(normals);f=np.concatenate(faces);path=out/row['mesh'];np.savez_compressed(path,vertices_mm=v,normals=n,faces=f,source_face=np.asarray(source))
  new=copy.deepcopy(row);new.update(vertices=len(v),triangles=len(f),mesh_sha256=sha(path),bounds_mm=[v.min(0).tolist(),v.max(0).tolist()],exact_master_face_ids=sorted(chosen));records.append(new);print(row['name'],len(f),'triangles;protected faces',len(chosen),flush=True)
 report.update(components=records,total_triangles=sum(r['triangles'] for r in records),method='hybrid CAD tessellation: coarse0.35mm/0.35rad plus exact original0.20mm/0.15rad on12camera-near source faces',protected_source_faces=select)
 (out/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
