import copy,itertools,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from dfalab import fault_atlas as fa
from dfalab import conformance as cf
from test_conformance import equivalent

ROOT=Path(__file__).resolve().parents[1]
CONTROLS=json.loads((ROOT/'docs/fault-atlas-controls.json').read_text())
class AtlasTests(unittest.TestCase):
 def test_controls_and_independent_coverage(self):
  for c in CONTROLS:
   r=fa.analyze(c['input']);self.assertTrue(fa.verify(r));ref=c['input']['reference'];faults=[]
   for t in r['candidates']:
    self.assertEqual(t['counterexample']is None,equivalent(ref,t['machine']))
    if t['counterexample']is not None:faults.append(t)
   for s in r['subsets']:
    survivors=[t['id']for t in faults if not(set(s['tests'])&set(t['rejected_by']))];self.assertEqual(s['missed_faults'],len(survivors))
   best=min((s['count'],s['symbols'])for s in r['subsets']if s['missed_faults']==0);self.assertEqual(best,(r['summary']['minimum_tests'],r['summary']['minimum_symbols_at_minimum_tests']))
  r=fa.analyze(CONTROLS[0]['input']);self.assertEqual(r['summary']['candidates'],128);self.assertEqual(r['summary']['equivalent'],40);self.assertEqual(r['summary']['faults'],88);self.assertEqual([r['words'][j]for j in r['subsets'][r['chosen_mask']]['tests']],['','a','b'])
  r=fa.analyze(CONTROLS[4]['input']);self.assertEqual(r['summary']['candidates'],648);self.assertEqual(r['summary']['equivalent'],6)
 def test_every_tiny_minimal_reference(self):
  # Every one/two-state unary or binary minimal reachable reference. For each,
  # independently inspect all maximal-domain candidates and all optimal masks.
  total=0
  for k in [1,2]:
   for n in [1,2]:
    for flat in itertools.product(range(n),repeat=n*k):
     for f in range(1<<n):
      for start in range(n):
       d={'alphabet':['a','b'][:k],'transitions':[list(flat[q*k:(q+1)*k])for q in range(n)],'start':start,'accept':[q for q in range(n)if f>>q&1]}
       try:cf.request({'reference':d,'implementation':d,'bound':n})
       except ValueError:continue
       r=fa.analyze({'reference':d,'bound':3 if k==1 else 2});self.assertTrue(fa.verify(r));total+=1
       for t in r['candidates']:self.assertEqual(t['counterexample']is None,equivalent(d,t['machine']))
  self.assertEqual(total,60)
 def test_verifier_disabled_generators_and_forgery(self):
  r=fa.analyze(CONTROLS[1]['input'])
  with patch.object(fa,'analyze',side_effect=AssertionError),patch.object(fa,'conformance',side_effect=AssertionError),patch.object(fa,'product',side_effect=AssertionError),patch.object(fa,'path',side_effect=AssertionError),patch.object(cf,'analyze',side_effect=AssertionError):self.assertTrue(fa.verify(r))
  for change in [lambda r:r['candidates'].pop(),lambda r:r['candidates'][0]['outputs'].__setitem__(0,1),lambda r:r['candidates'][0].update(counterexample=None),lambda r:r['subsets'][0].update(missed_faults=0),lambda r:r['optimal_masks'].append(0),lambda r:r.update(chosen_mask=True),lambda r:r['chosen_necessity'].pop(),lambda r:r['summary'].update(equivalent=0),lambda r:r['words'].pop(),lambda r:r['suite_certificate']['tests'].pop(),lambda r:r['full_suite_essential'].append(99)]:
   t=copy.deepcopy(r);change(t);self.assertFalse(fa.verify(t))
 def test_strict_input_and_cli(self):
  x=CONTROLS[0]['input']
  for c in [{},None,[],{**x,'bound':True},{**x,'bound':2.0},{**x,'bound':3},{**x,'extra':0},{'reference':{'alphabet':['a'],'transitions':[[0],[1]],'start':0,'accept':[0]},'bound':2}]:
   with self.assertRaises((ValueError,TypeError)):fa.analyze(c)
  for c in [None,{},True,[],{'schema':'dfalab-fault-atlas-v1'}]:self.assertFalse(fa.verify(c))
  with tempfile.TemporaryDirectory()as td:
   p=Path(td)/'request.json';o=Path(td)/'report.json';p.write_text(json.dumps(x));cmd=[sys.executable,'-m','dfalab.fault_atlas',str(p),'--output',str(o)];self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,0);self.assertTrue(fa.verify(json.loads(o.read_text())));self.assertEqual(subprocess.run([sys.executable,'-m','dfalab.fault_atlas',str(o),'--verify'],capture_output=True).stdout,b'valid\n');before=o.read_bytes();p.write_bytes(b' '*65537);self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,2);self.assertEqual(o.read_bytes(),before)
