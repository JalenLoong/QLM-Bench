"""Local review of completed diagnostic Raw captures, including genuine failures."""
import argparse
import importlib.util
import json
from pathlib import Path
from http.server import ThreadingHTTPServer

spec=importlib.util.spec_from_file_location('push_preview',Path(__file__).with_name('push_box_scaleup_preview.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class PilotPreview(module.Preview):
    def __init__(self,roots,page):
        super().__init__(roots[0].parent/'engineering-preview-v2',page)
        self.roots=roots;self.details={};self.loaded=set()

    def refresh(self):
        with self.lock:
            for number,root in enumerate(self.roots,1):
                for result in sorted((root/'attempts').glob('*/result.json')):
                    key=f'r{number}__'+result.parent.name.split('__a')[0]
                    if key in self.loaded:continue
                    uid=result.parent.name.split('__a')[0];raw=result.parent/'raw'/uid
                    if not (raw/'capture.json').exists():continue
                    data=json.loads(result.read_text());capture=json.loads((raw/'capture.json').read_text())
                    assert capture['diagnostic_only']
                    refs={}
                    for view,role in [('ego','ego'),('task','task_centric'),('observer','observer')]:
                        video=capture['videos'][role];path=Path(video['final'])
                        if not path.exists():path=Path(video['partial'])
                        refs[view+'.mp4']=path
                    for view,role in [('ego','ego'),('task','task_centric')]:refs[view+'-terminal.png']=raw/'review'/f'terminal_pre_reset_{role}.png'
                    phases=[];last=None
                    for command in capture['commands']:
                        phase=command['extensions']['expert'].get('phase')
                        if phase and phase!=last:phases.append({'name':phase,'seconds':command['start_tick']/500});last=phase
                    metadata=capture['profile']['scaleup_metadata'];side=capture['profile']['scaleup_goal_recovery']['side']
                    self.rows.append({'uid':key,'source':f'r{number}','round_label':f'第{number}轮','side':side,
                        'metadata':metadata,'frames':capture['videos']['ego']['count'],'duration':capture['videos']['ego']['count']/50,
                        'outcome':data['outcome'],'status':'engineering_only','recovery_verified':bool(data['recovery_verified'] and data['outcome']=='success'),
                        'approach_max_step_m':data.get('approach_max_native_target_step_m'),'attempt':1})
                    self.media[key]=refs;self.details[key]={'phases':phases,'recovery':None,'observer_available':True}
                    self.loaded.add(key)

    def catalog(self):
        self.refresh();running=[]
        for number,root in enumerate(self.roots,1):
            p=root/'progress.json'
            if p.exists():
                d=json.loads(p.read_text())
                for row in d['lanes']:
                    key=f'r{number}__'+row['uid']
                    if key not in self.loaded:running.append({'round':number,'uid':row['uid'],'seconds':row['simulation_seconds'],'phase':row['phase']})
        return {'pilot':True,'accepted':0,'new':0,'historical':0,'target':100,'episodes':self.rows,'running':running}

    def detail(self,uid):
        self.refresh();return self.details[uid]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--round-root',action='append',type=Path,required=True);p.add_argument('--page',type=Path,required=True);p.add_argument('--port',type=int,default=8767);args=p.parse_args()
    preview=PilotPreview(args.round_root,args.page.resolve());server=ThreadingHTTPServer(('127.0.0.1',args.port),module.handler(preview))
    print(json.dumps({'url':f'http://127.0.0.1:{args.port}/','diagnostics':len(preview.catalog()['episodes']),'formal_dataset':False}),flush=True)
    server.serve_forever()


if __name__=='__main__':main()
