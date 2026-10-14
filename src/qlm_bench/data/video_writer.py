from pathlib import Path
import subprocess
import numpy as np
from qlm_bench.compatibility.dataset_v2.validation import PROFILE, digest
from qlm_bench.compatibility.rgb_profiles import RGB_HW, dataset_profile, LEGACY_RGB

class VideoSink:
    def __init__(self,path,ffmpeg,fps,*,rgb_profile=LEGACY_RGB):
        self.rgb_profile=rgb_profile
        self.height,self.width=RGB_HW[rgb_profile]
        self.profile=dataset_profile(PROFILE,rgb_profile)
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        self.partial=self.path.with_suffix('.partial.mp4');self.count=0
        if self.path.exists() or self.partial.exists():raise ValueError('Refuse overwrite')
        crf=18 if fps==50 else 23
        self.command=[ffmpeg,'-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{self.width}x{self.height}','-framerate',str(fps),'-i','pipe:0','-vf','scale=in_range=full:out_range=tv:out_color_matrix=bt709','-c:v','libx264','-threads','2','-crf',str(crf),'-preset','medium']
        if fps==50:self.command+=['-g','50','-keyint_min','50','-sc_threshold','0']
        self.command+=['-pix_fmt','yuv420p','-color_range','tv','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-fps_mode','cfr',str(self.partial)]
        self.errors=self.partial.with_suffix('.encoder.log').open('x')
        self.proc=subprocess.Popen(self.command,stdin=subprocess.PIPE,stderr=self.errors)
        self.receipt=dict(profile_hash=digest(self.profile['policy_video']) if fps==50 else None,encoder='libx264',crf=crf,
                          preset='medium',gop=50 if fps==50 else None,keyint_min=50 if fps==50 else None,
                          scenecut=0 if fps==50 else None,color_range='tv',command=self.command,
                          encoder_version=subprocess.check_output([ffmpeg,'-version'],text=True).splitlines()[0])
    def write(self,rgb):
        if rgb.dtype!=np.uint8 or rgb.shape!=(self.height,self.width,3):raise ValueError('RGB8 shape')
        self.proc.stdin.write(np.ascontiguousarray(rgb).tobytes());self.count+=1
    def close(self):
        close_error=None
        try:self.proc.stdin.close()
        except (BrokenPipeError,OSError) as error:close_error=error
        try:code=self.proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.proc.kill();code=self.proc.wait();close_error=RuntimeError('Encoder did not finish within30s')
        finally:self.errors.close()
        if close_error:raise RuntimeError(f'Encoder close failed {self.partial}: {close_error}') from close_error
        if code:raise RuntimeError(f'Encoder failed {self.partial}')
        # Only the offline full-video validator may rename the partial.
        return dict(partial=str(self.partial),final=str(self.path),count=self.count,receipt=self.receipt)
