"""Read STEP/XCAF assemblies, preserve transforms and export selected BRep shapes."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time

import numpy as np
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepTools import BRepTools
from OCP.IFSelect import IFSelect_ReturnStatus
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_Label, TDF_LabelSequence, TDF_Tool
from OCP.TDocStd import TDocStd_Document
from OCP.TopLoc import TopLoc_Location
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ShapeTool
from OCP.TopAbs import TopAbs_ShapeEnum
from OCP.TopExp import TopExp_Explorer


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def matrix(location):
    t=location.Transformation();a=np.eye(4)
    for i in range(3):
        for j in range(4):a[i,j]=t.Value(i+1,j+1)
    return a.tolist()


def label_name(label):
    attr=TDataStd_Name()
    if label.FindAttribute(TDataStd_Name.GetID_s(),attr):return attr.Get().ToExtString()
    return ''


def label_id(label):
    from OCP.TCollection import TCollection_AsciiString
    s=TCollection_AsciiString();TDF_Tool.Entry_s(label,s);return s.ToCString()


def shape_info(shape):
    b=Bnd_Box();BRepBndLib.Add_s(shape,b,False)
    counts={}
    for name,kind in [('solids',TopAbs_ShapeEnum.TopAbs_SOLID),('shells',TopAbs_ShapeEnum.TopAbs_SHELL),('faces',TopAbs_ShapeEnum.TopAbs_FACE)]:
        e=TopExp_Explorer(shape,kind);n=0
        while e.More():n+=1;e.Next()
        counts[name]=n
    return {'bounds_mm':list(b.Get()),**counts}


def main():
    p=argparse.ArgumentParser();p.add_argument('--step',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    source=Path(a.step).resolve();identity={'work_id':'QLM-SIM-007','source':str(source),'source_sha256':sha(source),
       'source_bytes':source.stat().st_size,'OCP':importlib.metadata.version('cadquery-ocp'),
       'kind':'read_only_CAD_extraction','started_unix':time.time()}
    (out/'attempt.json').write_text(json.dumps(identity,indent=2)+'\n')
    print('Reading STEP',source.stat().st_size,'bytes',flush=True)
    reader=STEPCAFControl_Reader();reader.SetNameMode(True);reader.SetColorMode(True)
    status=reader.ReadFile(str(source))
    if status!=IFSelect_ReturnStatus.IFSelect_RetDone:raise ValueError('STEP reader status:'+str(status))
    print('Read complete, transferring XCAF',flush=True)
    doc=TDocStd_Document(TCollection_ExtendedString('MDTV-XCAF'))
    if not reader.Transfer(doc):raise ValueError('STEP transfer failed')
    tool=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main());free=TDF_LabelSequence();tool.GetFreeShapes(free)
    records=[]
    def visit(label,parent,depth=0):
        ref=TDF_Label();isref=XCAFDoc_ShapeTool.GetReferredShape_s(label,ref)
        target=ref if isref else label
        local=XCAFDoc_ShapeTool.GetLocation_s(label)
        global_loc=parent.Multiplied(local)
        name=label_name(target) or label_name(label)
        shape=XCAFDoc_ShapeTool.GetShape_s(target)
        # Definition shape's own location is retained; component location is applied once.
        located=shape.Moved(global_loc)
        record={'name':name,'label':label_id(label),'definition_label':label_id(target),'depth':depth,
                'is_reference':isref,'assembly':XCAFDoc_ShapeTool.IsAssembly_s(target),
                'component_location_mm':matrix(local),'global_location_mm':matrix(global_loc),
                'definition_shape_location_mm':matrix(shape.Location()),'shape':shape_info(located)}
        if depth>0 and not record['assembly']:
            filename=f'component-{len(records):02}.brep'
            if not BRepTools.Write_s(located,str(out/filename)):raise ValueError('BRep export failed')
            record['brep']=filename;record['brep_sha256']=sha(out/filename)
        records.append(record);print('Component',name,record['shape'],flush=True)
        children=TDF_LabelSequence()
        if XCAFDoc_ShapeTool.GetComponents_s(target,children,False):
            for i in range(1,children.Length()+1):visit(children.Value(i),global_loc,depth+1)
    for i in range(1,free.Length()+1):visit(free.Value(i),TopLoc_Location())
    if sha(source)!=identity['source_sha256']:raise ValueError('Original STEP changed')
    report={**identity,'passed':True,'units':'OpenCascade default millimetres, STEP source SI_UNIT MILLI METRE',
            'components':records,'elapsed_s':time.time()-identity['started_unix']}
    (out/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Assembly extracted',len(records),'records',flush=True)


if __name__=='__main__':main()
