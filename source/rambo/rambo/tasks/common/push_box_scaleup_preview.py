"""Read-only localhost review of accepted Push demonstrations, with MP4 seeking."""
from __future__ import annotations
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import threading
from urllib.parse import urlsplit


class Preview:
    def __init__(self, root, page):
        self.root=root.resolve();self.page=page;self.thumb_root=self.root/'preview-v1/thumbnails'
        self.thumb_root.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock();self.rows=[];self.media={};self.entries={};self.stamp=None

    def refresh(self):
        with self.lock:
            path=self.root/'accepted.json';stamp=path.stat().st_mtime_ns
            if stamp==self.stamp:return
            entries=json.loads(path.read_text());rows=[];media={}
            for row in sorted(entries,key=lambda r:r['episode_uid']):
                uid=row['episode_uid'];root=Path(row['canonical']);contract=json.loads((root/'meta/contract.json').read_text());ep=contract['episodes'][0]
                metadata=row['metadata'];duration=ep['length']/50
                rows.append(dict(uid=uid,source=row['source'],historical_uid=row.get('historical_episode_uid'),
                    attempt=row.get('accepted_attempt'),duration=duration,frames=ep['length'],metadata=metadata,status='accepted'))
                refs={}
                for name,key in [('ego','observation.images.ego'),('task','observation.images.task_centric')]:
                    refs[name+'.mp4']=root/ep['videos'][key]['path']
                    refs[name+'-terminal.png']=root/ep['terminal']['images'][key]['path']
                raw=Path(row['raw']);manifest=json.loads((raw/'manifest.json').read_text())
                if manifest['observer']['present']:refs['observer.mp4']=raw/manifest['observer']['path']
                media[uid]=refs
            self.rows=rows;self.media=media;self.entries={r['episode_uid']:r for r in entries};self.stamp=stamp

    def catalog(self):
        self.refresh()
        with self.lock:
            return {'accepted':len(self.rows),'new':sum(r['source']=='new' for r in self.rows),'historical':sum(r['source']=='historical' for r in self.rows),'target':100,'episodes':self.rows}

    def detail(self,uid):
        self.refresh();row=self.entries[uid];root=Path(row['canonical'])
        contract=json.loads((root/'meta/contract.json').read_text());ref=contract['extensions'].get('task_review')
        phases=[];recovery=None
        if ref:
            review=json.loads((root/ref['path']).read_text());last=None
            for command in review['commands']:
                phase=command.get('phase')
                if phase and phase!=last:
                    phases.append({'name':phase,'seconds':command['simulation_time_ns']/1e9});last=phase
                if command.get('recovery_evidence'):recovery=command['recovery_evidence']
        return {'phases':phases,'recovery':recovery,'observer_available':'observer.mp4' in self.media[uid]}

    def thumbnail(self,uid,view='task'):
        self.refresh();path=self.thumb_root/(uid+'-'+view+'.jpg')
        with self.lock:
            if not path.exists():
                import av
                with av.open(str(self.media[uid][view+'.mp4'])) as stream:
                    stream.streams.video[0].codec_context.thread_count=1
                    image=next(stream.decode(video=0)).to_image();image.thumbnail((384,216));image.save(path,quality=82)
        return path


def handler(preview):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_HEAD(self):self.respond(head=True)
        def do_GET(self):self.respond()
        def json(self,value,head=False):
            body=json.dumps(value,ensure_ascii=False,allow_nan=False).encode();self.send_response(200)
            self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store');self.end_headers()
            if not head:self.wfile.write(body)
        def file(self,path,head=False):
            size=path.stat().st_size;start=0;end=size-1;status=200
            requested=self.headers.get('Range')
            if requested:
                match=re.fullmatch(r'bytes=(\d*)-(\d*)',requested)
                if not match or not any(match.groups()):self.send_error(416);return
                a,b=match.groups()
                if a:start=int(a);end=min(int(b),end) if b else end
                else:start=max(0,size-int(b))
                if start>end or start>=size:self.send_error(416);return
                status=206
            mime={'.html':'text/html; charset=utf-8','.mp4':'video/mp4','.png':'image/png','.jpg':'image/jpeg'}[path.suffix]
            self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Accept-Ranges','bytes')
            self.send_header('Content-Length',str(end-start+1));self.send_header('Cache-Control','no-cache' if path.suffix=='.html' else 'private, max-age=3600')
            if status==206:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
            self.end_headers()
            if head:return
            with path.open('rb') as stream:
                stream.seek(start);remaining=end-start+1
                while remaining:
                    data=stream.read(min(1024*1024,remaining))
                    if not data:break
                    self.wfile.write(data);remaining-=len(data)
        def respond(self,head=False):
            path=urlsplit(self.path).path
            uid_pattern=r'((?:r[0-9]+__)?push_box__ep\d{4})'
            try:
                if path in ('/','/index.html'):return self.file(preview.page,head)
                if path=='/api/episodes':return self.json(preview.catalog(),head)
                match=re.fullmatch(r'/api/detail/'+uid_pattern,path)
                if match:return self.json(preview.detail(match[1]),head)
                match=re.fullmatch(r'/thumb/'+uid_pattern+r'\.jpg',path)
                if match:return self.file(preview.thumbnail(match[1]),head)
                match=re.fullmatch(r'/thumb/'+uid_pattern+r'/(ego|task)\.jpg',path)
                if match:return self.file(preview.thumbnail(match[1],match[2]),head)
                match=re.fullmatch(r'/media/'+uid_pattern+r'/(ego\.mp4|task\.mp4|observer\.mp4|ego-terminal\.png|task-terminal\.png)',path)
                if match:
                    preview.refresh();return self.file(preview.media[match[1]][match[2]],head)
                self.send_error(404)
            except (KeyError,FileNotFoundError):self.send_error(404)
            except (BrokenPipeError,ConnectionResetError):pass
    return Handler


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--page',type=Path,required=True);p.add_argument('--port',type=int,default=8766)
    args=p.parse_args();preview=Preview(args.root,args.page.resolve());server=ThreadingHTTPServer(('127.0.0.1',args.port),handler(preview))
    print(json.dumps({'url':f'http://127.0.0.1:{args.port}/','accepted':preview.catalog()['accepted'],'read_only_source':True}),flush=True)
    server.serve_forever()


if __name__=='__main__':main()
