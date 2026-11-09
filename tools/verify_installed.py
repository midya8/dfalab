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
