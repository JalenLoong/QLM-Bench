"""Read source STEP face/component colors without inventing a CAD material density."""
import argparse,json
from pathlib import Path

from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool,XCAFDoc_ShapeTool,XCAFDoc_ColorType,XCAFDoc_ColorTool
from OCP.TDF import TDF_Label,TDF_LabelSequence
from OCP.TopAbs import TopAbs_ShapeEnum
from OCP.TopExp import TopExp_Explorer
from OCP.Quantity import Quantity_Color

from inspect_step_assembly import sha,label_name


def main():
    p=argparse.ArgumentParser();p.add_argument('--step',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    reader=STEPCAFControl_Reader();reader.SetNameMode(True);reader.SetColorMode(True)
    print('Reading STEP colors',flush=True);reader.ReadFile(a.step)
    doc=TDocStd_Document(TCollection_ExtendedString('MDTV-XCAF'))
    if not reader.Transfer(doc):raise ValueError('STEP color transfer failed')
    shapes=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main());colors=XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    def rgb(item):
        for kind in (XCAFDoc_ColorType.XCAFDoc_ColorSurf,XCAFDoc_ColorType.XCAFDoc_ColorGen):
            c=Quantity_Color()
            found=XCAFDoc_ColorTool.GetColor_s(item,kind,c) if isinstance(item,TDF_Label) else colors.GetColor(item,kind,c)
            if found:return [c.Red(),c.Green(),c.Blue()]
        return None
    def visit(label):
        ref=TDF_Label();target=ref if XCAFDoc_ShapeTool.GetReferredShape_s(label,ref) else label
        name=label_name(target)
        if name in ('基础框架最终版1-6','单支架'):
            shape=XCAFDoc_ShapeTool.GetShape_s(target);fallback=rgb(target) or rgb(label)
            inherited=[]
            for kind in (TopAbs_ShapeEnum.TopAbs_SOLID,TopAbs_ShapeEnum.TopAbs_SHELL):
                owners=TopExp_Explorer(shape,kind)
                while owners.More():
                    color=rgb(owners.Current())
                    if color is not None:
                        faces=TopExp_Explorer(owners.Current(),TopAbs_ShapeEnum.TopAbs_FACE)
                        while faces.More():inherited.append((faces.Current(),color));faces.Next()
                    owners.Next()
            values=[];e=TopExp_Explorer(shape,TopAbs_ShapeEnum.TopAbs_FACE)
            while e.More():
                face=e.Current();color=rgb(face) or fallback
                if color is None:
                    color=next((c for owner,c in inherited if owner.IsSame(face)),None)
                values.append(color);e.Next()
            records[name]={'default_RGB':fallback,'face_RGB':values,'colorless_faces':sum(x is None for x in values)}
            print(name,'faces',len(values),'colorless',records[name]['colorless_faces'],flush=True)
        children=TDF_LabelSequence()
        if XCAFDoc_ShapeTool.GetComponents_s(target,children,False):
            for i in range(1,children.Length()+1):visit(children.Value(i))
    records={};free=TDF_LabelSequence();shapes.GetFreeShapes(free)
    for i in range(1,free.Length()+1):visit(free.Value(i))
    (out/'result.json').write_text(json.dumps({'STEP_sha256':sha(a.step),'components':records,'passed':True},ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
