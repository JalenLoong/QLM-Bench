"""Original Isaac task assets/cooked collision -> portable MuJoCo candidate.

No collision decomposition or visual decimation is performed. Source PhysX hulls,
UVs/material textures and runtime inertia are carried explicitly into the pack.
Backend contact compliance and renderer response still require actual validation.
"""
import argparse
import copy
import itertools
import json
from pathlib import Path
import shutil
import traceback
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
from PIL import Image
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation

from build_original_robot import mesh_parts, numbers, primitive, quat, sha


def value(node,name,default=None):
    v=node.get('attributes',{}).get(name,{}).get('value',default)
    return default if v is None else v


def shader_node(material):
    candidates=[(p,n) for p,n in material['nodes'].items() if n['type']=='Shader' and
                (value(n,'info:id')=='UsdPreviewSurface' or value(n,'info:mdl:sourceAsset:subIdentifier')=='gltf_material')]
    if len(candidates)!=1:raise ValueError('Ambiguous material surface shader')
    return candidates[0][1]


class MaterialExporter:
    def __init__(self,asset,out,verified_sources):
        self.asset,self.out,self.verified_sources=asset,out,verified_sources
        self.cache={};self.records=[]
        (out/'textures').mkdir(exist_ok=True)

    def export(self,key,material):
        if key in self.cache:return self.cache[key]
        node=shader_node(material)
        color=value(node,'inputs:diffuseColor',value(node,'inputs:base_color_factor',[1.,1.,1.]))
        opacity=value(node,'inputs:opacity',value(node,'inputs:base_alpha',1.))
        roughness=value(node,'inputs:roughness',value(node,'inputs:roughness_factor',1.))
        metallic=value(node,'inputs:metallic',value(node,'inputs:metallic_factor',0.))
        # A connected scalar uses its texture rather than a zero fallback factor.
        connections=node.get('connections',{})
        if 'inputs:metallic' in connections:metallic=1.
        name='task_mat_'+str(len(self.cache))
        mat=ET.SubElement(self.asset,'material',name=name,rgba=numbers([*color,opacity]),
                         roughness=str(roughness),metallic=str(metallic),
                         specular=str(value(node,'inputs:specular',.5)),shininess=str(1.-min(1.,roughness)),texuniform='false')
        uv_sets=set();layers=[]
        mapping={'inputs:diffuseColor':('rgb',None),'inputs:base_color_texture':('rgb',None),
                 'inputs:normal':('normal',None),'inputs:normal_texture':('normal',None),
                 'inputs:roughness':('roughness',0),'inputs:metallic':('metallic',0)}
        for input_name,(role,channel) in mapping.items():
            if input_name not in connections:continue
            layer,uv=self.texture(material,connections[input_name],role,channel)
            ET.SubElement(mat,'layer',role=role,texture=layer);layers.append((role,layer));uv_sets.add(uv)
        if 'inputs:metallic_roughness_texture' in connections:
            for role,channel in [('roughness',1),('metallic',2)]:
                layer,uv=self.texture(material,connections['inputs:metallic_roughness_texture'],role,channel)
                ET.SubElement(mat,'layer',role=role,texture=layer);layers.append((role,layer));uv_sets.add(uv)
        if len(uv_sets)>1:raise ValueError('Multiple UV coordinate sets per material require explicit conversion')
        result={'name':name,'uv_name':next(iter(uv_sets),None)}
        self.cache[key]=result
        self.records.append({'source_material':key,'material':name,'source':material,'layers':layers,
                             'mapping':'Native material parameters and explicit original texture layers; RTX/MDL response is not pixel-equivalent'})
        return result

    def texture(self,material,connection,role,channel):
        if len(connection)!=1:raise ValueError('Multiple texture connections')
        node=material['nodes'][connection[0].rsplit('.',1)[0]]
        src=value(node,'inputs:file',value(node,'inputs:texture'))
        if not isinstance(src,dict) or not src.get('resolved_path'):raise ValueError('Unresolved original texture')
        path=Path(src['resolved_path']).resolve()
        if str(path) not in self.verified_sources or sha(path)!=self.verified_sources[str(path)]:
            raise ValueError('Texture is not in verified original resource inventory: '+str(path))
        if value(node,'inputs:offset',[0.,0.])!=[0.,0.] or value(node,'inputs:scale',[1.,1.]) not in ([1.,1.],[2.,2.,2.,2.]) or value(node,'inputs:rotation',0.)!=0.:
            raise ValueError('Unexpected UV transform')
        uv='st'
        if 'inputs:st' in node.get('connections',{}):
            uvnode=material['nodes'][node['connections']['inputs:st'][0].rsplit('.',1)[0]]
            uv=value(uvnode,'inputs:varname')
        elif value(node,'inputs:tex_coord_index',0)!=0:raise ValueError('Unexpected glTF texture coordinate set')
        name='task_tex_'+sha(path)[:16]+'_'+role
        dest=self.out/'textures'/(name+'.png')
        if not dest.exists():
            # Format/channel conversion only: no resize, filtering or color edits.
            image=Image.open(path).convert('RGB')
            if channel is not None:
                image=Image.merge('RGB',[image.getchannel(channel)]*3)
            image.save(dest)
            ET.SubElement(self.asset,'texture',name=name,type='2d',file='textures/'+dest.name)
        return name,uv


def mesh_transform(g,reference):
    transform=np.asarray(g['body_transform_row_major'],float).T
    body=reference['bodies'].get(g['body'])
    if body is not None:
        # USD's relative geometry transform excludes the owning body's scale.
        # Physics body frames are rigid; bake the authored scale into geometry.
        scale=np.asarray(value(body,'xformOp:scale',[1.,1.,1.]))
        transform=np.diag([*scale,1.])@transform
    return transform


def write_hull(path,vertices,counts,indices):
    faces=[];offset=0
    for count in counts:
        polygon=indices[offset:offset+count];offset+=count
        for i in range(1,int(count)-1):faces.append([polygon[0],polygon[i],polygon[i+1]])
    with path.open('x') as stream:
        stream.write('# Original PhysX cooked convex hull; no decomposition/simplification\n')
        np.savetxt(stream,vertices,fmt='v %.17g %.17g %.17g')
        np.savetxt(stream,np.asarray(faces)+1,fmt='f %d %d %d')
    return len(faces)


def build(robot_pack,reference,asset_reference,output):
    robot_pack,ref,asset_ref,out=map(Path,(robot_pack,reference,asset_reference,output))
    out.mkdir(parents=True,exist_ok=False)
    result={'work_id':'QLM-SIM-005','status':'started','builder_sha256':sha(__file__),
            'robot_pack':str(robot_pack.resolve()),'reference':str(ref.resolve())}
    (out/'attempt.json').write_text(json.dumps(result,indent=2)+'\n')
    try:
        source=json.loads((ref/'result.json').read_text());task=source['task'];p=source['profile']
        if source['status']!='completed' or not source['source_unchanged']:raise ValueError('Unchanged actual original reference required')
        reference_data=json.loads((ref/'task_usd/reference.json').read_text())
        cooked=json.loads((ref/'cooked_collision.json').read_text())
        for file,expected in [('task_physics.npz',source['physics_arrays_sha256']),('task_usd/reference.json',source['task_usd_sha256']),
                              ('task_usd/geometry.npz',reference_data['geometry_arrays_sha256']),('cooked_collision.json',source['cooked_collision_sha256']),
                              ('cooked_collision.npz',cooked['arrays_sha256'])]:
            if sha(ref/file)!=expected:raise ValueError('Original reference checksum changed: '+file)
        identity=json.loads((asset_ref/'identity.json').read_text());inventory=identity['verified_files'];source_root=Path(identity['source_root'])
        verified_sources={str((source_root/name).resolve()):rec['sha256'] for name,rec in inventory.items()}
        for path,expected in verified_sources.items():
            if sha(path)!=expected:raise ValueError('Original source payload changed: '+path)
        manifest=json.loads((robot_pack/'resource-manifest.json').read_text())
        for name,record in manifest['files'].items():
            if sha(robot_pack/name)!=record['sha256']:raise ValueError('Original robot resource checksum mismatch')
        shutil.copytree(robot_pack/'meshes',out/'meshes')
        tree=ET.parse(robot_pack/'go2.xml').getroot();world=tree.find('worldbody');asset=tree.find('asset')
        # A vertical spotlight retains real shadows while avoiding the grazing
        # floor self-shadow artifacts observed with the old diagonal light.
        # Camera, textures and all physical parameters remain unchanged.
        light=world.find('light');light.set('pos','.65 0 3');light.set('dir','0 0 -1')
        physics=np.load(ref/'task_physics.npz',allow_pickle=False)
        arrays=np.load(ref/'task_usd/geometry.npz',allow_pickle=False)
        hull_arrays=np.load(ref/'cooked_collision.npz',allow_pickle=False)
        materials=MaterialExporter(asset,out,verified_sources)
        initial_pose=physics['pose'][0].astype(float)
        initial_pose[3:]/=np.linalg.norm(initial_pose[3:])
        body=ET.SubElement(world,'body',name='primary',pos=numbers(initial_pose[:3]),quat=numbers(initial_pose[[6,3,4,5]]))
        inertia=physics['inertia'][0].reshape(3,3)
        ET.SubElement(body,'inertial',pos=numbers(physics['com'][0,:3]),mass=numbers(physics['mass'][0]),
                      fullinertia=numbers([inertia[0,0],inertia[1,1],inertia[2,2],inertia[0,1],inertia[0,2],inertia[1,2]]))
        if task=='press_button':
            body.set('gravcomp','1')
            ET.SubElement(body,'joint',name='button_slide',type='slide',axis='1 0 0',range=numbers([0,p['stroke_m']]),stiffness='0',damping='0')
            # This is the original internal mechanical spring, not an assistance
            # force. The force cap is retained, unlike an unlimited joint spring.
            ET.SubElement(tree.find('actuator'),'general',name='button_spring',joint='button_slide',gainprm='0',
                          biastype='affine',biasprm=numbers([0,-p['spring_stiffness_N_m'],-p['spring_damping_N_s_m']]),
                          forcelimited='true',forcerange=numbers([-p['max_effort_N'],p['max_effort_N']]),ctrllimited='false')
        else:ET.SubElement(body,'freejoint',name='object_free')
        static_body=ET.SubElement(world,'body',name='task_static')
        geometry_map=[];local_points=[];source_geom={g['id']:g for g in reference_data['geometries']}
        for g in reference_data['geometries']:
            transform=mesh_transform(g,reference_data)
            owner=body if g['body'] in reference_data['bodies'] else static_body
            points=arrays[g['points']]@transform[:3,:3].T+transform[:3,3]
            if owner is body:local_points.append(points)
            if g['visibility']=='invisible' or g['purpose'] not in ('default','render'):continue
            if g['material_subsets']:raise ValueError('Task material subsets need explicit per-subset UV binding')
            mat=materials.export(g['material'],reference_data['materials'][g['material']])
            exported=copy.deepcopy(g);exported['id']='task_'+g['id'];exported['body_transform_row_major']=transform.T.tolist()
            parts=mesh_parts(exported,arrays,out/'meshes',uv_name=mat['uv_name'])
            for part in parts:
                ET.SubElement(asset,'mesh',name=part['name'],file=part['file'],inertia='shell',maxhullvert='64')
                ET.SubElement(owner,'geom',name=part['name'],type='mesh',mesh=part['name'],material=mat['name'],contype='0',conaffinity='0',group='2')
            geometry_map.append({'source_geometry':g['path'],'role':'visual','parts':parts})
        hull_records=[]
        for shape in cooked['shapes']:
            g=source_geom[shape['source_geometry']];transform=mesh_transform(g,reference_data)
            owner=body if g['body'] in reference_data['bodies'] else static_body
            physmat=reference_data['materials'].get(shape.get('physics_material'),{})
            friction=value(physmat,'physics:dynamicFriction',1.)
            static_friction=value(physmat,'physics:staticFriction',friction)
            for hull in shape['hulls']:
                vertices=hull_arrays[hull['vertices']]@transform[:3,:3].T+transform[:3,3]
                name='original_collision_'+hull['id'];path=out/'meshes'/(name+'.obj')
                face_count=write_hull(path,vertices,hull_arrays[hull['face_counts']],hull_arrays[hull['face_indices']])
                ET.SubElement(asset,'mesh',name=name,file='meshes/'+path.name,inertia='shell')
                # Robot=1/2; task dynamic=2/7; static=4/3. Disable only the
                # original button cap vs housing pair; no invisible constraints.
                bits=('2','1') if task=='press_button' and owner is body else ('4','1') if task=='press_button' else ('2','7')
                ET.SubElement(owner,'geom',name=name,type='mesh',mesh=name,group='3',rgba='.7 .2 .2 0',
                              contype=bits[0],conaffinity=bits[1],friction=numbers([friction,0.,0.]),condim='3',priority='1')
                hull_records.append({'name':name,'source_geometry':g['path'],'source_hull':hull['id'],
                                     'vertices':len(vertices),'faces':face_count,'static_friction_source':static_friction,
                                     'dynamic_friction':friction,'physics_material':physmat,'sha256':sha(path)})
        base=world.find("body[@name='base']")
        rig=json.loads((ref/'camera_rig_usd/reference.json').read_text())
        if not np.allclose(rig['root_local_transform_row_major'],np.eye(4)):raise ValueError('Unexpected camera rig root transform')
        for i,g in enumerate(rig['geometries']):
            if g['collision_enabled']:raise ValueError('Original rig unexpectedly has physical collisions')
            node=shader_node(rig['materials'][g['material']]);color=value(node,'inputs:diffuseColor')
            ET.SubElement(base,'geom',name='original_camera_rig_'+str(i),**primitive(g),rgba=numbers([*color,1.]),contype='0',conaffinity='0',group='2')
        for name in source['extras']:
            extra=json.loads((ref/('extra_'+name)/'reference.json').read_text())
            for i,g in enumerate(extra['geometries']):
                prepared=copy.deepcopy(g)
                prepared['body_transform_row_major']=(np.asarray(g['root_transform_row_major'])@np.asarray(extra['root_local_transform_row_major'])).tolist()
                node=shader_node(extra['materials'][g['material']]);color=value(node,'inputs:diffuseColor')
                ET.SubElement(world,'geom',name='original_'+name+'_'+str(i),**primitive(prepared),rgba=numbers([*color,1.]),
                              contype='4' if g['collision_enabled'] else '0',conaffinity='3' if g['collision_enabled'] else '0',group='0')
        observer=source.get('observer')
        if observer is None:raise ValueError('Original runtime Observer reference is required')
        transform=np.asarray(observer['world_transform_row_major']).T;a=observer['attributes']
        # A render product sets the aspect ratio; derive the original vertical
        # FoV from its horizontal aperture at the fixed1280x720 resolution.
        f=float(a['focalLength']['value']);horizontal=float(a['horizontalAperture']['value'])
        vfov=np.degrees(2*np.arctan(horizontal*720/1280/(2*f)))
        actual_camera_parameters=source.get('renderer_camera_parameters')
        if actual_camera_parameters is None:raise ValueError('Actual RTX projection/view parameters required')
        projection=np.asarray(actual_camera_parameters['observer']['cameraProjection']).reshape(4,4)
        measured_vfov=np.degrees(2*np.arctan(1/projection[1,1]))
        if abs(vfov-measured_vfov)>1e-4:raise ValueError('Observer render-product projection differs from declared aperture')
        vfov=measured_vfov
        ET.SubElement(world,'camera',name='observer',pos=numbers(transform[:3,3]),quat=quat(transform[:3,:3]),fovy=str(vfov))
        profile={'schema':'qlm-mujoco-original-task-v1','task_id':task,
                 'instruction':{'push_box':'Push the box into the target area.','press_button':'Press the button.','lift_basket':'Lift the basket.'}[task],
                 'asset_id':p['asset_id'],'asset_profile':'original-isaac-'+task+'-candidate-v1',
                 'status':'engineering_candidate_not_pilot_frozen','source_profile':p,
                 'source_asset':identity['source_asset_manifest'],'source_runtime_sha256':sha(ref/'result.json'),
                 'robot_resource_sha256':sha(robot_pack/'resource-manifest.json'),
                 'rendering_profile':{'version':'native-overhead-spot-v1','light_position_m':[.65,0.,3.],
                                      'light_direction':[0.,0.,-1.],'shadows_enabled':True,
                                      'rationale':'remove grazing floor self-shadow artifacts; preserve texture, camera and geometry'},
                 'renderer_camera_parameters':actual_camera_parameters,
                 'horizon_s':24.,'force_zero':True,'success_hold_commands':p['success_policy_ticks'],
                 'fall':p['fall'],'mass_kg':float(physics['mass'][0,0]),'initial_object_pose_xyzw':initial_pose.tolist(),
                 'canonical_goal_position':source['initial_state']['task.goal.position'],
                 'mjwarp_capacity':{'nconmax':1024,'njmax':8192},
                 'observer':{'name':'observer','fps':25,'model_input':False,'source':observer,
                             'clipping_m':observer['attributes']['clippingRange']['value']},
                 'camera_rig':{'geometries':5,'reference_sha256':source['rig_usd_sha256']},
                 'contact_mapping':{'source_cooked_hulls':len(hull_records),'decomposition_recomputed':False,
                                    'friction':'source dynamic coefficient; explicit priority against floor/robot coefficient1',
                                    'static_dynamic_transition':'not identical to PhysX; behavior validation required',
                                    'compliance':'candidate MuJoCo contact solver settings; source stiffness/damping preserved in provenance; task behavior acceptance pending'}}
        all_points=np.concatenate(local_points)
        if task=='push_box':
            low,high=all_points.min(0),all_points.max(0)
            center=(low+high)/2;face=center.copy();face[0]=low[0]
            profile.update(bounds_local=[low.tolist(),high.tolist()],center_local=center.tolist(),face_center_local=face.tolist(),
                           goal_x=p['goal_x'],goal_y=p['goal_y'])
        elif task=='lift_basket':
            support=all_points[ConvexHull(all_points).vertices]
            r=Rotation.from_quat(source['primary_orientation']).as_matrix();upright=all_points@r.T
            handle=all_points[upright[:,2]>upright[:,2].min()+.18];handle=handle[ConvexHull(handle).vertices]
            profile.update(support_vertices_local=support.tolist(),handle_vertices_local=handle.tolist(),
                           initial_orientation_xyzw=source['primary_orientation'],minimum_clearance_m=p['minimum_clearance_m'],
                           floor_z_m=p['floor_z_m'],success_enable_after_s=p['success_enable_after_s'])
        else:
            profile.update(stroke_m=p['stroke_m'],threshold_m=p['success_displacement_m'],
                           button_rest_front_xyz=p['button_rest_front_xyz'],spring_stiffness_N_m=p['spring_stiffness_N_m'],
                           spring_damping_N_s_m=p['spring_damping_N_s_m'],max_effort_N=p['max_effort_N'])
        xml=out/'scene.xml';ET.indent(tree);ET.ElementTree(tree).write(xml,encoding='unicode')
        model=mujoco.MjModel.from_xml_path(str(xml));mapping=tree.find('visual/map')
        mapping.set('znear',str(.1/model.stat.extent));mapping.set('zfar',str(20/model.stat.extent))
        ET.indent(tree);ET.ElementTree(tree).write(xml,encoding='unicode')
        model=mujoco.MjModel.from_xml_path(str(xml));data=mujoco.MjData(model);mujoco.mj_forward(model,data)
        primary=model.body('primary');np.testing.assert_allclose(primary.mass,physics['mass'][0],atol=1e-9,rtol=0)
        np.testing.assert_allclose(primary.ipos,physics['com'][0,:3],atol=1e-9,rtol=0)
        rotation=Rotation.from_quat(primary.iquat[[1,2,3,0]]).as_matrix()
        np.testing.assert_allclose(rotation@np.diag(primary.inertia)@rotation.T,inertia,atol=1e-8,rtol=0)
        from scipy.spatial.distance import directed_hausdorff
        collision_errors=[]
        for h in hull_records:
            mesh=model.mesh(h['name']);geom=model.geom(h['name'])
            # MuJoCo centers/rotates mesh vertices. Reconstruct the original
            # parent-body coordinates before comparing to the PhysX hull.
            verts=model.mesh_vert[mesh.vertadr[0]:mesh.vertadr[0]+mesh.vertnum[0]]
            r=Rotation.from_quat(geom.quat[[1,2,3,0]]).as_matrix();compiled=verts@r.T+geom.pos
            s=next(s for s in cooked['shapes'] if any(x['id']==h['source_hull'] for x in s['hulls']))
            hull=next(x for x in s['hulls'] if x['id']==h['source_hull']);t=mesh_transform(source_geom[s['source_geometry']],reference_data)
            expected=hull_arrays[hull['vertices']]@t[:3,:3].T+t[:3,3]
            error=max(directed_hausdorff(compiled,expected)[0],directed_hausdorff(expected,compiled)[0])
            if error>2e-6:raise ValueError('Cooked collision geometry changed: '+h['name']+' '+str(error))
            collision_errors.append(error)
        (out/'scene.task.json').write_text(json.dumps(profile,indent=2)+'\n')
        (out/'geometry-map.json').write_text(json.dumps({'visual':geometry_map,'collision':hull_records,'materials':materials.records},indent=2)+'\n')
        shutil.copytree(ref,out/'source/runtime')
        shutil.copyfile(asset_ref/'identity.json',out/'source/asset-identity.json')
        shutil.copyfile(robot_pack/'go2.profile.json',out/'source/robot-profile.json')
        files={str(f.relative_to(out)):{'sha256':sha(f),'size_bytes':f.stat().st_size} for f in sorted(out.rglob('*')) if f.is_file() and not (f.parent==out and f.name in ('attempt.json','result.json'))}
        (out/'resource-manifest.json').write_text(json.dumps({'schema':'qlm-portable-mujoco-resource-v1','entrypoint':'scene.xml','files':files},indent=2)+'\n')
        result.update(status='completed',task=task,source_convex_hulls=len(hull_records),collision_vertex_max_error_m=max(collision_errors),
                      original_visual_nondegenerate_faces=sum(p['source_faces'] for g in geometry_map for p in g['parts']),
                      primary_mass_kg=float(primary.mass[0]),rig_geometries=5,observer_restored=True,
                      acceptance='static_mapping_only; actual task and renderer gates pending',resource_manifest_sha256=sha(out/'resource-manifest.json'))
    except BaseException as error:
        result.update(status='failed',error=repr(error),traceback=traceback.format_exc());raise
    finally:(out/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('robot-pack','reference','asset-reference','output'):p.add_argument('--'+name,required=True)
    a=p.parse_args();print(json.dumps(build(a.robot_pack,a.reference,a.asset_reference,a.output),indent=2))
