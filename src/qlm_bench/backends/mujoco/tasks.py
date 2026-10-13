"""Three MuJoCo engineering candidates with real contacts and retained predicates."""
from pathlib import Path
import hashlib
import itertools
import json
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
from qlm_bench.tasks.predicates import physical_condition
from qlm_bench.compatibility.dataset_v2.task_state import push_progress
from qlm_bench.tasks.success import PolicySuccessHold,PressSuccessHold


INSTRUCTIONS={'push_box':'Push the box into the target area.','press_button':'Press the button.',
              'lift_basket':'Lift the basket.'}


def build_task(reference_model, output, task_id):
    if task_id not in INSTRUCTIONS:raise ValueError('Only P2 three-task engineering candidates')
    output=Path(output)
    if output.exists():raise FileExistsError(output)
    xml=ET.parse(reference_model).getroot();world=xml.find('worldbody')
    profile={'schema':'qlm-mujoco-task-candidate-v1','task_id':task_id,'instruction':INSTRUCTIONS[task_id],
        'asset_id':'qlm-parametric-'+task_id,'license':'CC-BY-NC-4.0','source':'QLM authored procedural geometry',
        'asset_profile':'mujoco-p2-parametric-r2','status':'engineering_candidate_not_pilot_frozen',
        'success_hold_commands':3,'force_zero':True,'horizon_s':24.,
        'fall':{'base_height_lt':.1,'projected_gravity_error_gt':.75}}
    if task_id=='push_box':
        half=[.1503815,.087269,.113232]
        body=ET.SubElement(world,'body',name='primary',pos=f'.6903815 .142 {half[2]+.02}')
        ET.SubElement(body,'freejoint',name='object_free')
        ET.SubElement(body,'geom',name='task_object',type='box',size=' '.join(map(str,half)),mass='.207',
                      friction='.65 .005 .001',rgba='.68 .4 .18 1',condim='3')
        ET.SubElement(world,'site',name='goal',type='box',pos='1.15 .15 .001',size='.2 .25 .001',rgba='0 .8 0 .25')
        profile.update(half_extent=half,goal_x=[.95,1.35],goal_y=[-.1,.4],mass_kg=.207,
                       success='full pose-transformed footprint in goal, not fallen, three50Hz ticks')
    elif task_id=='press_button':
        ET.SubElement(world,'geom',name='button_housing',type='box',pos='.635 .1 .3',size='.04 .07 .07',rgba='.2 .25 .3 1')
        body=ET.SubElement(world,'body',name='primary',pos='.566 .1 .3')
        ET.SubElement(body,'joint',name='button_slide',type='slide',axis='1 0 0',range='0 .02',
                      stiffness='300',damping='8',springref='0')
        ET.SubElement(body,'geom',name='task_object',type='cylinder',size='.0442614 .006',
                      quat='.70710678 0 .70710678 0',mass='.1',rgba='.9 .05 .05 1',friction='.8 .005 .001')
        # The cap cannot collide with its surrounding housing; robot contact remains enabled.
        body.find('geom').set('contype','2');body.find('geom').set('conaffinity','1')
        world.find("geom[@name='button_housing']").set('contype','4')
        world.find("geom[@name='button_housing']").set('conaffinity','1')
        profile.update(stroke_m=.02,threshold_m=.012,press_axis_world=[1.,0.,0.],mass_kg=.1,
                       spring_stiffness_N_m=300.,spring_damping_N_s_m=8.,release_required=False,
                       success='actual axial displacement>=12mm, not fallen, three50Hz ticks')
    else:
        body=ET.SubElement(world,'body',name='primary',pos='.75 .15 .02')
        ET.SubElement(body,'freejoint',name='object_free')
        # An open basket with a front handle aperture; collision never closes the opening.
        parts=[('floor',[0,0,.012],[.12,.13,.012]),
               ('left',[0,-.125,.075],[.12,.006,.075]),('right',[0,.125,.075],[.12,.006,.075]),
               ('back',[.114,0,.075],[.006,.12,.075]),('front',[-.114,0,.055],[.006,.12,.055]),
               ('handle_left',[0.,-.064,.19],[.008,.008,.08]),
               ('handle_right',[0.,.064,.19],[.008,.008,.08]),
               ('handle_top',[0.,0,.27],[.008,.072,.008])]
        for name,pos,size in parts:
            ET.SubElement(body,'geom',name='basket_'+name,type='box',pos=' '.join(map(str,pos)),
                          size=' '.join(map(str,size)),mass=str(.53/len(parts)),
                          friction='.8 .005 .001',rgba='.15 .5 .8 1',condim='3')
        profile.update(minimum_clearance_m=.02,floor_z_m=0.,mass_kg=.53,
                       handle_local={'x':0.,'half_thickness':.008,'inner_y':[-.056,.056],'inner_z':[.11,.262]},
                       parts=[{'name':n,'position':p,'half_extent':s} for n,p,s in parts],
                       success='whole basket geometry minimum worldZ>=2cm, not fallen, three50Hz ticks',
                       interaction='complete FL foot threading before upward handle support')
    output.parent.mkdir(parents=True,exist_ok=True);ET.indent(xml)
    ET.ElementTree(xml).write(output,encoding='unicode')
    profile['xml_sha256']=hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.task.json').write_text(json.dumps(profile,indent=2)+'\n')
    return output


class TaskState:
    def __init__(self,physics,profile):
        self.physics=physics;self.profile=profile;self.task=profile['task_id']
        m=physics.model
        self.body=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_BODY,'primary')
        self.hold=np.zeros(physics.count,dtype=int)
        self.through=np.zeros(physics.count,dtype=bool)
        self.initial_center_x=np.zeros(physics.count,dtype=float)
        self.success_holds=[PressSuccessHold(profile['threshold_m']) if self.task=='press_button'
                            else PolicySuccessHold(profile.get('success_hold_commands',3))
                            for _ in range(physics.count)]
        self.reset()

    def reset(self,indices=None):
        """Capture each lane's real reset center after its physics reset."""
        indices=range(self.physics.count) if indices is None else indices
        for index in indices:
            self.hold[index]=0;self.through[index]=False
            self.success_holds[index].reset()
            self.initial_center_x[index]=self.geometric_center(index)[0]

    def progress(self,index):
        p,_,corners=self.geometry(index)
        if self.task=='push_box':return push_progress(self.geometric_center(index)[0],self.initial_center_x[index])
        if self.task=='press_button':
            joint=mujoco.mj_name2id(self.physics.model,mujoco.mjtObj.mjOBJ_JOINT,'button_slide')
            return float(self.physics.data[index].qpos[self.physics.model.jnt_qposadr[joint]])
        return float(corners[:,2].min()-self.profile['floor_z_m'])

    def geometry(self,index):
        d=self.physics.data[index];p=d.xpos[self.body];r=d.xmat[self.body].reshape(3,3)
        if self.task=='push_box':
            bounds=self.profile.get('bounds_local')
            local=np.array(list(itertools.product(*zip(*bounds)))) if bounds is not None else np.array(list(itertools.product(*[[-h,h] for h in self.profile['half_extent']])))
            corners=local@r.T+p
        elif self.task=='lift_basket':
            if 'support_vertices_local' in self.profile:
                local=np.asarray(self.profile['support_vertices_local'])
            else:
                local=np.concatenate([np.array(list(itertools.product(*[[-h,h] for h in part['half_extent']])))+
                                      part['position'] for part in self.profile['parts']])
            corners=local@r.T+p
        else:corners=np.array([p])
        return p,r,corners

    def geometric_center(self,index):
        p,r,corners=self.geometry(index)
        if self.task=='push_box' and 'center_local' in self.profile:
            return p+r@np.asarray(self.profile['center_local'])
        if self.task=='lift_basket':return (corners.min(0)+corners.max(0))/2
        if self.task=='press_button' and 'button_rest_front_xyz' in self.profile:
            result=np.asarray(self.profile['button_rest_front_xyz'],dtype=float).copy()
            result[0]+=self.progress(index)
            return result
        return p

    def evaluate(self,index,core):
        p,r,corners=self.geometry(index)
        fallen=bool(core.base_height[index]<.1 or np.linalg.norm(core.projected_gravity_b[index].cpu().numpy()-[0,0,-1])>.75)
        displacement=0.
        if self.task=='press_button':
            joint=mujoco.mj_name2id(self.physics.model,mujoco.mjtObj.mjOBJ_JOINT,'button_slide')
            displacement=float(self.physics.data[index].qpos[self.physics.model.jnt_qposadr[joint]])
        condition,progress=physical_condition(self.task,self.profile,corners_world=corners,
            displacement=displacement,time_s=float(self.physics.ticks[index])*.002,
            center_x=self.geometric_center(index)[0],initial_center_x=self.initial_center_x[index])
        hold=self.success_holds[index]
        success=hold.update(int(self.physics.ticks[index]),
                            displacement if self.task=='press_button' else condition,not fallen)
        self.hold[index]=hold.count
        return {'success':bool(success),'fallen':fallen,'progress':progress,
                'timed_out':bool(self.physics.ticks[index]*.002>=self.profile['horizon_s'])}
