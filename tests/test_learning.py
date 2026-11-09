import copy
import itertools
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from dfalab import learn,verify
from dfalab import core

ROOT=Path(__file__).resolve().parents[1]

def oracle(d):
    """Classic pair-marking minimization, no observation table or product BFS."""
    n=len(d['transitions']);pairs={(p,q) for p in range(n) for q in range(p+1,n) if (p in d['accept'])!=(q in d['accept'])}
    while True:
        new=set(pairs)
        for p in range(n):
            for q in range(p+1,n):
                if any(tuple(sorted((d['transitions'][p][k],d['transitions'][q][k]))) in pairs for k in range(len(d['alphabet']))):new.add((p,q))
        if pairs==new:break
        pairs=new
    reachable={d['start']}
    while True:
        new=reachable|{z for q in reachable for z in d['transitions'][q]}
        if new==reachable:break
        reachable=new
    classes=[]
    for p in sorted(reachable):
        if all(tuple(sorted((p,q))) in pairs for q in classes):classes.append(p)
    return len(classes),pairs,reachable


def run(d,w):
    q=d['start']
    for c in w:q=d['transitions'][q][d['alphabet'].index(c)]
    return q in d['accept']

class LearningTests(unittest.TestCase):
    def check_case(self,d):
        original=copy.deepcopy(d);r=learn(d);self.assertEqual(d,original);self.assertTrue(verify(r));h=r['final']
        self.assertEqual(len(h['transitions']),oracle(d)[0]);self.assertEqual(r['stats']['equivalence_queries'],sum(s['action']['kind']=='conjecture' for s in r['steps']))
        # Complete language equivalence via fixed-point distinguishability in the
        # disjoint union, separate from the certificate product construction.
        off=len(d['transitions']);u={'transitions':d['transitions']+[[x+off for x in row] for row in h['transitions']], 'alphabet':d['alphabet'],'start':d['start'],'accept':d['accept']+[x+off for x in h['accept']]}
        self.assertNotIn(tuple(sorted((d['start'],h['start']+off))),oracle(u)[1])
        eqs=[s['action']['hypothesis']['dfa'] for s in r['steps'] if s['action']['kind']=='conjecture'];self.assertTrue(all(len(a['transitions'])<len(b['transitions']) for a,b in zip(eqs,eqs[1:])))
        for s in r['steps']:
            if s['action']['kind']!='conjecture':continue
            a=s['action'];w=a['equivalence']['counterexample']
            if w is not None:
                self.assertNotEqual(run(d,w),run(a['hypothesis']['dfa'],w))
                # Independently enumerate every shorter/earlier word, not BFS.
                for k in range(len(w)+1):
                    for cs in itertools.product(d['alphabet'],repeat=k):
                        v=''.join(cs)
                        if (len(v),v)>=(len(w),w):break
                        self.assertEqual(run(d,v),run(a['hypothesis']['dfa'],v))
        return r

    def test_all_two_state_binary(self):
        for ts in itertools.product(range(2),repeat=4):
            for f in range(4):
                for start in range(2):self.check_case({'alphabet':['a','b'],'transitions':[list(ts[:2]),list(ts[2:])],'start':start,'accept':[i for i in range(2) if f>>i&1]})

    def test_all_three_state_binary(self):
        for ts in itertools.product(range(3),repeat=6):
            for f in range(8):
                for start in range(3):self.check_case({'alphabet':['a','b'],'transitions':[list(ts[k:k+2]) for k in range(0,6,2)],'start':start,'accept':[i for i in range(3) if f>>i&1]})

    def test_all_three_state_unary(self):
        for ts in itertools.product(range(3),repeat=3):
            for f in range(8):
                for start in range(3):self.check_case({'alphabet':['a'],'transitions':[[x] for x in ts],'start':start,'accept':[i for i in range(3) if f>>i&1]})

    def test_seeded_larger_teachers(self):
        rng=random.Random(1987)
        for n in [3,4,5,6]:
            for _ in range(100):self.check_case({'alphabet':['a','b','c'],'transitions':[[rng.randrange(n) for _ in range(3)] for _ in range(n)],'start':rng.randrange(n),'accept':[i for i in range(n) if rng.randrange(2)]})

    def test_controls_mechanisms(self):
        controls=json.loads((ROOT/'docs/controls.json').read_text());kinds=set()
        for c in controls:
            r=self.check_case(c['target']);kinds.update(s['action']['kind'] for s in r['steps'])
        self.assertEqual(kinds,{'closure','consistency','conjecture'})
        self.assertTrue(any(learn(c['target'])['stats']['equivalence_queries']>=3 for c in controls))

    def test_independent_verifier_and_forgery(self):
        d=json.loads((ROOT/'docs/controls.json').read_text())[2]['target'];r=learn(d)
        with patch.object(core,'learn',side_effect=AssertionError),patch.object(core,'table',side_effect=AssertionError),patch.object(core,'hypothesis',side_effect=AssertionError),patch.object(core,'product',side_effect=AssertionError),patch.object(core,'minimal',side_effect=AssertionError),patch.object(core,'path',side_effect=AssertionError):self.assertTrue(verify(r))
        def mutate(f):
            v=copy.deepcopy(r);f(v);self.assertFalse(verify(v))
        mutate(lambda v:v.update(schema='other'));mutate(lambda v:v.update(extra=1));mutate(lambda v:v['steps'][0]['queries'][0].update(answer=1));mutate(lambda v:v['steps'][0]['queries'][0]['path'].__setitem__(0,True));mutate(lambda v:v['steps'][0]['rows'][0]['bits'].__setitem__(0,1));mutate(lambda v:v['stats'].update(membership_queries=0));mutate(lambda v:v['steps'].pop());mutate(lambda v:v['final']['transitions'][0].__setitem__(0,True));mutate(lambda v:v['minimality']['access'].__setitem__(0,'b'));mutate(lambda v:v['minimality']['distinctions'].pop());mutate(lambda v:v['steps'][-1]['action']['equivalence']['edges'][0].__setitem__(0,True));mutate(lambda v:v['steps'][-1]['action']['equivalence']['pairs'].pop())

    def test_invalid_requests(self):
        d={'alphabet':['a'],'transitions':[[0]],'start':0,'accept':[]}
        for key,bad in [('alphabet',[]),('alphabet',['a','a']),('alphabet',['b','a']),('alphabet',['A']),('alphabet',['ab']),('alphabet',[1]),('transitions',[]),('transitions',[[False]]),('transitions',[[1]]),('transitions',[[0,0]]),('start',True),('start',1),('accept',[False]),('accept',[0,0]),('accept',[1]),('transitions',[[0]]*7)]:
            v=copy.deepcopy(d);v[key]=bad
            with self.assertRaises(ValueError):learn(v)
        with self.assertRaises(ValueError):learn(dict(d,unknown=1))
        for bad in [None,[],{},True,{'schema':'dfalab-learning-v1'}]:self.assertFalse(verify(bad))

    def test_cli_atomic_and_limits(self):
        d={'alphabet':['a'],'transitions':[[0]],'start':0,'accept':[]}
        with tempfile.TemporaryDirectory() as td:
            inp=Path(td)/'in.json';out=Path(td)/'out.json';inp.write_text(json.dumps(d));cmd=[sys.executable,'-m','dfalab',str(inp),'--output',str(out)]
            self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,0);r=json.loads(out.read_text());self.assertTrue(verify(r));self.assertEqual(subprocess.run([sys.executable,'-m','dfalab',str(out),'--verify'],capture_output=True).stdout,b'valid\n')
            before=out.read_bytes()
            for raw in [b'{',b'{"alphabet":[],"alphabet":[]}',b' '*65537,b'NaN',b'{}']:
                inp.write_bytes(raw);self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,2);self.assertEqual(out.read_bytes(),before)
            inp.write_bytes(b' '* (8*1024*1024+1));self.assertEqual(subprocess.run([sys.executable,'-m','dfalab',str(inp),'--verify'],capture_output=True).returncode,2)

if __name__=='__main__':unittest.main()
