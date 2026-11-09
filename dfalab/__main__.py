import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from .core import learn, verify

def main():
    p=argparse.ArgumentParser(description='Exact observation-table DFA learning and independent trace verification')
    p.add_argument('input');p.add_argument('--verify',action='store_true');p.add_argument('--output');a=p.parse_args()
    try:
        cap=8*1024*1024 if a.verify else 65536
        with open(a.input,'rb') if a.input!='-' else __import__('contextlib').nullcontext(sys.stdin.buffer) as source:
            raw=source.read(cap+1)
        if len(raw)>cap:raise ValueError('input exceeds size limit')
        def unique(pairs):
            d={}
            for k,v in pairs:
                if k in d:raise ValueError('duplicate JSON key')
                d[k]=v
            return d
        d=json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
        if a.verify:
            if not verify(d):raise ValueError('invalid learning certificate')
            out='valid\n'
        else:out=json.dumps(learn(d),indent=2,ensure_ascii=True)+'\n'
        if a.output:
            target=Path(a.output); fd,name=tempfile.mkstemp(prefix='.'+target.name+'.',dir=target.parent)
            try:
                with os.fdopen(fd,'w') as f:f.write(out)
                os.replace(name,target)
            finally:
                if os.path.exists(name):os.unlink(name)
        else:sys.stdout.write(out)
    except (ValueError,OSError,TypeError,KeyError,RecursionError) as e:
        print('dfalab: '+str(e),file=sys.stderr);return 2
    return 0
if __name__=='__main__':raise SystemExit(main())
