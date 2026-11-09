"""Outside-checkout generation and independent certificate checking."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import dfalab
import dfalab.core
import dfalab.__main__
from dfalab import learn,verify
assert all('site-packages' in str(Path(m.__file__).resolve()) for m in [dfalab,dfalab.core,dfalab.__main__])
controls=json.loads(Path(sys.argv[1]).read_text())
with tempfile.TemporaryDirectory() as td:
 for i,c in enumerate(controls):
  p=Path(td)/'request.json';p.write_text(json.dumps(c['target']));expected=learn(c['target']);assert verify(expected)
  for cmd in [[sys.executable,'-m','dfalab'],[sys.argv[2]]]:
   out=Path(td)/'report.json';subprocess.run(cmd+[str(p),'--output',str(out)],check=True,capture_output=True);assert json.loads(out.read_text())==expected
   v=subprocess.run(cmd+[str(out),'--verify'],check=True,capture_output=True,text=True);assert v.stdout=='valid\n'
print(f'Installed: {len(controls)} controls, both generation/verification entry points, three site-packages origins, outside checkout')

import dfalab.conformance
from dfalab.conformance import analyze,verify as check_conformance
assert 'site-packages' in str(Path(dfalab.conformance.__file__).resolve())
controls=json.loads(Path(sys.argv[3]).read_text())
with tempfile.TemporaryDirectory() as td:
 for c in controls:
  p=Path(td)/'request.json';p.write_text(json.dumps(c['input']));expected=analyze(c['input']);assert check_conformance(expected)
  for cmd in [[sys.executable,'-m','dfalab.conformance'],[sys.argv[4]]]:
   out=Path(td)/'conformance.json';subprocess.run(cmd+[str(p),'--output',str(out)],check=True,capture_output=True);assert json.loads(out.read_text())==expected
   assert subprocess.run(cmd+[str(out),'--verify'],check=True,capture_output=True,text=True).stdout=='valid\n'
print(f'Installed conformance: {len(controls)} controls, both entry points, fourth site-packages origin, outside checkout')

import dfalab.fault_atlas
from dfalab.fault_atlas import analyze as atlas,verify as check_atlas
assert 'site-packages' in str(Path(dfalab.fault_atlas.__file__).resolve())
controls=json.loads(Path(sys.argv[5]).read_text())
with tempfile.TemporaryDirectory() as td:
 for c in controls:
  p=Path(td)/'request.json';p.write_text(json.dumps(c['input']));expected=atlas(c['input']);assert check_atlas(expected)
  for cmd in [[sys.executable,'-m','dfalab.fault_atlas'],[sys.argv[6]]]:
   out=Path(td)/'atlas.json';subprocess.run(cmd+[str(p),'--output',str(out)],check=True,capture_output=True);assert json.loads(out.read_text())==expected
   assert subprocess.run(cmd+[str(out),'--verify'],check=True,capture_output=True,text=True).stdout=='valid\n'
print(f'Installed fault atlas: {len(controls)} controls, both entry points, fifth site-packages origin, outside checkout')
