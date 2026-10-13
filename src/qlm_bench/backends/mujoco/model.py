"""Versioned Go2 derivation from a verified Menagerie resource pack."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET


def build_go2(source_root, output, *, task="reference"):
    source_root, output = Path(source_root), Path(output)
    if output.exists():
        raise FileExistsError(output)
    manifest = json.loads((source_root/"source-manifest.json").read_text())
    for name, record in manifest["files"].items():
        if hashlib.sha256((source_root/name).read_bytes()).hexdigest() != record["sha256"]:
            raise ValueError("Go2 resource checksum mismatch: "+name)
    xml = ET.parse(source_root/"go2.xml").getroot()
    xml.find("compiler").set("meshdir",str((source_root/"assets").resolve()))
    option = xml.find("option")
    option.set("timestep","0.002")
    option.set("integrator","implicitfast")
    # Physical joint losses must not duplicate the explicit retained motor model.
    xml.find("default/default/geom").set("margin","0")
    joint = xml.find("default/default/joint")
    joint.set("damping","0")
    joint.set("frictionloss","0")
    xml.remove(xml.find("keyframe"))
    world = xml.find("worldbody")
    ET.SubElement(world,"light",pos="1 -1 3",dir="-1 1 -2",diffuse=".8 .8 .8")
    ET.SubElement(world,"geom",name="floor",type="plane",size="4 4 .1",rgba=".35 .4 .45 1",friction="1 .02 .01",condim="3")
    base = world.find("body")
    base.set("pos","0 0 .4")
    import numpy as np
    from scipy.spatial.transform import Rotation
    frozen_profile=json.loads((Path(__file__).resolve().parents[2]/"compatibility/dataset_v2/spec/profile.json").read_text())
    camera_from_optical=np.diag([1.,-1.,-1.])
    for name,profile in frozen_profile["policy_camera_geometry"].items():
        mount=Rotation.from_quat(profile["mount_quaternion_xyzw"]).as_matrix()
        optical=np.asarray(profile["R_mount_from_optical"],dtype=float)
        rotation=Rotation.from_matrix(mount@optical@camera_from_optical).as_quat()
        fovy=np.degrees(2*np.arctan(profile["height"]/(2*profile["intrinsics"][1][1])))
        ET.SubElement(base,"camera",name=name,pos=" ".join(map(str,profile["mount_position_m"])),
                      quat=" ".join(map(str,rotation[[3,0,1,2]])),fovy=str(fovy))
    for leg in ("FL","FR","RL","RR"):
        calf=base.find(f".//body[@name='{leg}_calf']")
        # A named fixed foot frame preserves the source sphere and its exact pose.
        foot=ET.SubElement(calf,"body",name=leg+"_foot",pos="0 0 -.213")
        # Source calf inertial already includes this collision geometry. A new
        # fixed coordinate frame must not infer and double-count its mass.
        ET.SubElement(foot,"inertial",pos="0 0 0",mass="0",diaginertia="0 0 0")
        for geom in list(calf.findall("geom")):
            if geom.get("name")==leg:
                calf.remove(geom);geom.set("pos","-.002 0 0");foot.append(geom)
    output.parent.mkdir(parents=True,exist_ok=True)
    ET.indent(xml)
    ET.ElementTree(xml).write(output,encoding="unicode")
    import mujoco
    original=mujoco.MjModel.from_xml_path(str(source_root/"go2.xml"))
    derived=mujoco.MjModel.from_xml_path(str(output))
    if not np.isclose(original.body_mass.sum(),derived.body_mass.sum(),atol=1e-10,rtol=0):
        raise ValueError("Go2 coordinate-frame derivation changed total robot mass")
    record={"schema":"qlm-go2-mujoco-derivative-v1","source":manifest,"task":task,
        "changes":["physics2ms/implicitfast","explicit RAMBO motor owns joint damping/delay/saturation",
                   "zero contact margins for MJWarp MULTICCD compatibility","fixed named foot frames","ground and mounted cameras","reset root height0.4m"],
        "xml_sha256":hashlib.sha256(output.read_bytes()).hexdigest(),"acceptance":"pending"}
    output.with_suffix('.profile.json').write_text(json.dumps(record,indent=2)+'\n')
    return output
