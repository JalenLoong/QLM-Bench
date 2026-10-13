"""Independent case streams; sampling distributions and controller math are retained."""
import hashlib
import torch


class CaseRandomStreams:
    version='rambo-case-rng-v1'

    def __init__(self,seeds):
        self.seeds=[None]*len(seeds)
        self.streams={name:[None]*len(seeds) for name in ('motor_delay','qp_regularizer')}
        self.counts={name:[0]*len(seeds) for name in self.streams}
        self.reset(range(len(seeds)),seeds)

    @staticmethod
    def validate_seed(seed):
        if type(seed) is not int or not 0<=seed<2**63:raise ValueError('Case seed must be an integer in[0,2**63)')
        return seed

    def reset(self,ids,seeds):
        ids=[int(i) for i in ids];seeds=list(seeds)
        if len(ids)!=len(seeds) or len(ids)!=len(set(ids)) or any(i<0 or i>=len(self.seeds) for i in ids):
            raise ValueError('Unique lanes and one explicit seed per lane required')
        for i,seed in zip(ids,seeds):
            self.seeds[i]=self.validate_seed(seed)
            for name in self.streams:
                digest=hashlib.sha256(f'{self.version}:{seed}:{name}'.encode()).digest()
                generator=torch.Generator(device='cpu');generator.manual_seed(int.from_bytes(digest[:8],'big')%(2**63))
                self.streams[name][i]=generator;self.counts[name][i]=0

    def motor_delays(self,ids,device):
        if not len(ids):return torch.empty((0,2),dtype=torch.long,device=device)
        rows=[]
        for i in map(int,ids):
            rows.append(torch.randint(0,11,(2,),generator=self.streams['motor_delay'][i]))
            self.counts['motor_delay'][i]+=2
        return torch.stack(rows).to(device)

    def qp_uniform(self,device):
        values=[]
        for i,generator in enumerate(self.streams['qp_regularizer']):
            values.append(torch.rand(1,generator=generator));self.counts['qp_regularizer'][i]+=1
        return torch.stack(values).to(device).reshape(-1,1,1)

    def identity(self):
        return {'version':self.version,'case_seeds':list(self.seeds),'generator':'Torch CPU; domain-separated SHA256 seeds',
                'draw_counts':{k:list(v) for k,v in self.counts.items()},
                'state_sha256':{k:[hashlib.sha256(g.get_state().numpy().tobytes()).hexdigest() for g in values]
                                for k,values in self.streams.items()},
                'motor_distribution':'two independent UniformInteger[0,10] per case reset: calf then hip/thigh',
                'QP_distribution':'Uniform[0,1) times original1e-6 diagonal regularizer, one draw per case/controller call'}
