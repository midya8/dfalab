import copy
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from dfalab import core
from dfalab.conformance import analyze,verify
from dfalab import conformance as cf
from test_learning import oracle

ROOT=Path(__file__).resolve().parents[1]

def equivalent(r,i):
    n=len(r['transitions']);u={'alphabet':r['alphabet'],'transitions':r['transitions']+[[x+n for x in row] for row in i['transitions']], 'start':r['start'],'accept':r['accept']+[x+n for x in i['accept']]}
    return tuple(sorted((r['start'],i['start']+n))) not in oracle(u)[1]

class ConformanceTests(unittest.TestCase):
    def check(self,x):
        before=copy.deepcopy(x);r=analyze(x);self.assertEqual(x,before);self.assertTrue(verify(r));s=r['summary'];self.assertEqual(s['exact_equivalent'],equivalent(x['reference'],x['implementation']))
        if s['bound_holds']:self.assertEqual(s['suite_passed'],s['exact_equivalent'])
        if s['exact_equivalent']:self.assertTrue(s['suite_passed'])
        self.assertEqual(s['tests'],len(set(t['word'] for t in r['tests'])));self.assertEqual(s['cartesian_products'],len(r['state_cover'])*len(r['characterization'])*len(r['middle_words']))
        return r

    def test_all_binary_three_state_implementations(self):
        # Several independently minimal references, all 3-state transition,
        # acceptance and start choices. Their actual reachable counts are used.
        refs=[{'alphabet':['a','b'],'transitions':[[0,0]],'start':0,'accept':[]},{'alphabet':['a','b'],'transitions':[[0,0]],'start':0,'accept':[0]},{'alphabet':['a','b'],'transitions':[[1,0],[0,1]],'start':0,'accept':[0]}]
        for ts in itertools.product(range(3),repeat=6):
            for f in range(8):
                for start in range(3):
                    impl={'alphabet':['a','b'],'transitions':[list(ts[k:k+2]) for k in range(0,6,2)],'start':start,'accept':[i for i in range(3) if f>>i&1]}
                    # Direct theorem check with independent word enumeration,
                    # not running/report-comparing the full generator 52k times.
                    for ref in refs:
                        n=len(ref['transitions']);access=[''] if n==1 else ['','a'];W=[''];words=set(p+''.join(mid)+w for p in access for k in range(3-n+2) for mid in itertools.product(ref['alphabet'],repeat=k) for w in W)
                        def run(d,w):
                            q=d['start']
                            for c in w:q=d['transitions'][q][d['alphabet'].index(c)]
                            return q in d['accept']
                        passed=all(run(ref,w)==run(impl,w) for w in words);self.assertEqual(passed,equivalent(ref,impl))

    def test_complete_reports_controls_and_seeded(self):
        for c in json.loads((ROOT/'docs/conformance-controls.json').read_text()):self.check(c['input'])
        rng=random.Random(1978)
        refs=[c['input']['reference'] for c in json.loads((ROOT/'docs/conformance-controls.json').read_text())]
        for _ in range(200):
            ref=rng.choice(refs);n=rng.randrange(1,7);a=ref['alphabet'];i={'alphabet':a[:],'transitions':[[rng.randrange(n) for _ in a] for _ in range(n)],'start':rng.randrange(n),'accept':[q for q in range(n) if rng.randrange(2)]};self.check({'reference':ref,'implementation':i,'bound':rng.randrange(len(ref['transitions']),7)})

    def test_bound_failure_and_unreachable_states(self):
        cs=json.loads((ROOT/'docs/conformance-controls.json').read_text());r=self.check(cs[0]['input']);self.assertTrue(r['summary']['suite_passed']);self.assertFalse(r['summary']['bound_holds']);self.assertFalse(r['summary']['exact_equivalent']);self.assertEqual(r['equivalence']['counterexample'],'aaa')
        r=self.check(cs[1]['input']);self.assertFalse(r['summary']['suite_passed']);self.assertTrue(r['summary']['bound_holds'])
        r=self.check(cs[4]['input']);self.assertTrue(r['summary']['bound_holds']);self.assertEqual(r['summary']['implementation_reachable_states'],1)

    def test_independent_verification_and_forgery(self):
        x=json.loads((ROOT/'docs/conformance-controls.json').read_text())[2]['input'];r=analyze(x)
        with patch.object(cf,'analyze',side_effect=AssertionError),patch.object(cf,'request',side_effect=AssertionError),patch.object(cf,'accesses',side_effect=AssertionError),patch.object(cf,'product',side_effect=AssertionError),patch.object(cf,'separation',side_effect=AssertionError),patch.object(cf,'path',side_effect=AssertionError):self.assertTrue(verify(r))
        def mutation(f):
            c=copy.deepcopy(r);f(c);self.assertFalse(verify(c))
        mutation(lambda c:c.update(extra=1));mutation(lambda c:c['tests'].pop());mutation(lambda c:c['characterization'].append('aa'));mutation(lambda c:c['middle_words'].pop());mutation(lambda c:c['tests'][0].update(expected=1));mutation(lambda c:c['tests'][0]['reference_path'].__setitem__(0,True));mutation(lambda c:c['tests'][0]['factors'].update(middle='a'));mutation(lambda c:c['summary'].update(bounded_equivalence_certificate=0));mutation(lambda c:c['equivalence']['edges'][0].__setitem__(0,True));mutation(lambda c:c['pair_distinctions'].pop());mutation(lambda c:c['reference_access'][0].update(word='a'))

    def test_strict_input(self):
        x=json.loads((ROOT/'docs/conformance-controls.json').read_text())[2]['input']
        for k,v in [('bound',True),('bound',1),('bound',7),('bound',2.0),('reference',{'alphabet':['a'],'transitions':[[1],[1]],'start':0,'accept':[]}),('reference',{'alphabet':['a'],'transitions':[[0],[1]],'start':0,'accept':[0]})]:
            c=copy.deepcopy(x);c[k]=v
            with self.assertRaises(ValueError):analyze(c)
        for v in [None,{},True,[],{'schema':'dfalab-conformance-v1'}]:self.assertFalse(verify(v))

    def test_cli_transport(self):
        c=json.loads((ROOT/'docs/conformance-controls.json').read_text())[0]['input']
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'request.json';out=Path(td)/'report.json';p.write_text(json.dumps(c));cmd=[sys.executable,'-m','dfalab.conformance',str(p),'--output',str(out)];self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,0);self.assertTrue(verify(json.loads(out.read_text())));self.assertEqual(subprocess.run([sys.executable,'-m','dfalab.conformance',str(out),'--verify'],capture_output=True).stdout,b'valid\n');before=out.read_bytes();p.write_text('{}');self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,2);self.assertEqual(out.read_bytes(),before)
            p.write_bytes(b' '*65537);self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,2);self.assertEqual(out.read_bytes(),before)
            p.write_bytes(b' '*(8*1024*1024+1));self.assertEqual(subprocess.run([sys.executable,'-m','dfalab.conformance',str(p),'--verify'],capture_output=True).returncode,2)
