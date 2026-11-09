"""Generate only original synthetic fixtures; does not run on package install."""
import random,json
from pathlib import Path
from dfalab import learn
controls=[]
def add(name,note,ts,accept,start=0,a=['a','b']):controls.append({'name':name,'note':note,'target':{'alphabet':a,'transitions':ts,'start':start,'accept':accept}})
add('Nothing is accepted','Equivalent rejecting states collapse; table needs no repair.',[[1,0],[0,1]],[])
add('Every word is accepted','Even the empty word is accepted; all reachable states merge.',[[1,0],[0,1]],[0,1])
add('Two parity bits','The standard even/even parity example from Angluin: a stable table can still give a wrong conjecture.',[[1,2],[0,3],[3,0],[2,1]],[0])
add('Delayed acceptance','Words shorter than five all look alike. A finite test prefix is not equivalence.',[[1],[2],[3],[4],[5],[5]],[5],a=['a'])
add('Unreachable accepting state','An accepting state exists but is unreachable. Language minimization discards it.',[[0,0],[1,1]],[1])
add('Starts away from zero','State labels are not semantics; start state is explicit.',[[0,1],[1,0]],[0],start=1)
add('Ends with ab','Reset behavior makes the last two symbols matter.',[[1,0],[1,2],[1,0]],[2])
add('Unary modulo three','The shortest separating suffix may be empty.',[[1],[2],[0]],[0],a=['a'])
rng=random.Random(1987)
for j in range(10000):
 n=6;d={'alphabet':['a','b','c'],'transitions':[[rng.randrange(n) for _ in range(3)] for _ in range(n)],'start':0,'accept':[q for q in range(n) if rng.randrange(2)]};r=learn(d)
 if r['stats']['equivalence_queries']>=3 and r['stats']['consistency_repairs']>=2:
  controls.append({'name':'Three experiments, one language','note':'Original seeded synthetic teacher. Multiple counterexamples and consistency repairs are needed.','target':d});break
else:raise AssertionError('no difficult control')
Path('docs/controls.json').write_text(json.dumps(controls,indent=2)+'\n')
for c in controls:print(c['name'],learn(c['target'])['stats'])
