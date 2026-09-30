"""Independent CPU audit of a physical Press Button pilot; never changes source data."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--raw',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    c=json.loads((args.raw/'capture.json').read_text());s=json.loads((args.raw/'summary.json').read_text());profile=c['profile'];rows=c['boundaries'];commands=c['commands'];n=len(commands)
    report={'work_id':c['work_id'],'passed':False,'task_success':False,'actions':n,'boundaries':len(rows),'contact':'unknown diagnostic only','errors':[]}
    def check(condition,message):
        if not condition:report['errors'].append(message)
    check(s.get('passed') and s.get('terminal_before_reset'),'collector and terminal-before-reset')
    check(c['mode'] in ('pilot','demonstration') and c['diagnostic_only']==(c['mode']=='pilot'),'data scope')
    check(c['task_text']=='Press the button.','task text')
    check(n>0 and len(rows)==n+1,'N actions / N+1 boundaries')
    check(s['reset_events']==['reset_enter_after_terminal_copy','reset_exit'],'reset event ordering')
    check(not c['terminal']['partial_interval'],'no partial last action')
    initial=np.asarray(rows[0]['state']['task.object.position']);axis=np.asarray(profile['press_axis_world']);goal=np.asarray(profile['button_rest_front_xyz'])+axis*profile['success_displacement_m'];hold=0;first=None;displacements=[]
    for i,row in enumerate(rows):
        state=row['state'];ns=row['simulation_time_ns'];review=row['task_review'];d=float(np.dot(np.asarray(state['task.object.position'])-initial,axis));displacements.append(d)
        check(ns==row['physics_step']*2_000_000,'authoritative physics timestamp')
        if i:check(ns-rows[i-1]['simulation_time_ns']==20_000_000,'policy cadence')
        check(np.allclose(state['task.goal.position'],goal,atol=1e-6),'button target mapping')
        check(abs(state['task.progress'][0]-d)<2e-6 and abs(review['button_displacement_m']-d)<2e-6,'independent axial displacement')
        check(np.allclose((np.asarray(state['task.object.position'])-initial)[1:],0,atol=1e-3),'prismatic lateral lock')
        check(-1e-3<=d<=profile['stroke_m']+1e-3,'reviewed stroke bounds')
        upright=state['observation.state.base.position'][2]>=.1 and np.linalg.norm(np.asarray(state['observation.state.projected_gravity'])-[0,0,-1])<=.75
        pressed=d>=profile['success_displacement_m'];hold=hold+1 if pressed and upright else 0
        if pressed and upright and first is None:first=ns
        check(not state['task.success'][0] or hold>=3,'success requires3 consecutive policy ticks')
        contact=row['contact'];check(contact['status']=='unknown' and contact['valid'] is False and contact['fl_object'] is None and contact['body_object'] is None,'explicit unknown contact')
    if 'reviewed_clearance_m' in profile:
        check(max(displacements)<profile['reviewed_clearance_m'],'no visible cap/collar interpenetration')
    for i,cmd in enumerate(commands):
        check(cmd['status']=='completed' and cmd['start_tick']==rows[i]['physics_step'] and cmd['end_tick']==rows[i+1]['physics_step'],'complete command interval')
        check(np.all(np.asarray(cmd['executed'])[6:]==0),'force-zero')
    check(all(np.all(np.asarray(x['external_force'])==0) and np.all(np.asarray(x['external_torque'])==0) for x in c['physics']),'no external object wrench')
    for role in ['ego','task_centric']:
        ids=[x['sensor_frame_ids'][role] for x in rows];check(all(b>a for a,b in zip(ids,ids[1:])),'fresh policy sensor frames')
        png=np.asarray(Image.open(args.raw/'review'/f'terminal_pre_reset_{role}.png').convert('RGB'))
        check(hashlib.sha256(png.tobytes()).hexdigest()==c['terminal']['rgb_hashes'][role],'terminal owned RGB copy')
        check(s['terminal_vs_reset'][role]['mean_absolute_pixel_difference']>0,'terminal/reset RGB distinction')
    check(np.allclose(c['post_reset_state']['task.object.position'],initial,atol=1e-5),'button reset restored rest pose')
    check(c['terminal']['simulation_time_ns']==rows[-1]['simulation_time_ns'] and c['terminal']['state']==rows[-1]['state'],'terminal matches last boundary')
    report['success_threshold_m']=profile['success_displacement_m']
    report.update(task_success=bool(rows[-1]['state']['task.success'][0]) and hold>=3,status=c['status'],duration_s=rows[-1]['simulation_time_ns']/1e9,first_pressed_ns=first,terminal_displacement_m=displacements[-1],maximum_displacement_m=max(displacements),terminal_before_reset=bool(s.get('terminal_before_reset')),command_phases=sorted({x['extensions']['expert']['phase'] for x in commands}),initial_robot_xy=rows[0]['state']['observation.state.base.position'][:2])
    check(np.allclose(report['initial_robot_xy'],[0,0],atol=1e-6),'native robot origin')
    check(report['task_success'] and c['status']=='success','task successful')
    press=[x['extensions']['expert'] for x in commands if x['extensions']['expert']['phase']=='press']
    if press and 'base_stop_reference_x' in press[0]:
        refs=[x['base_stop_reference_x'] for x in press];check(max(refs)-min(refs)<1e-9,'press base target must remain frozen')
        report['motion_metrics']=dict(motion=profile.get('motion','baseline'),base_stop_reference_x=refs[0],reference_stop_distance_m=profile['button_rest_front_xyz'][0]-refs[0],terminal_actual_stop_distance_m=profile['button_rest_front_xyz'][0]-rows[-1]['state']['observation.state.base.position'][0],terminal_actual_foot_extension_m=rows[-1]['task_review']['actual_fl_eef_world'][0]-rows[-1]['state']['observation.state.base.position'][0],maximum_reference_extension_m=max(x['reference_extension_world_x'] for x in press),saturated_fraction=sum(x['reference_x_saturated'] for x in press)/len(press))
        check(report['motion_metrics']['maximum_reference_extension_m']<=.460001,'46cm reference limit')
    report['passed']=not report['errors'];args.output.mkdir(parents=True,exist_ok=False);(args.output/'behavior.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
