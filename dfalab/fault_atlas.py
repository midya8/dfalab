"""Exhaustive finite DFA fault domains and exact W-suite subset selection."""
import itertools
import json
from .core import validate,integer,product,path,same
from .conformance import analyze as conformance,verify as verify_conformance


def domain(x):
    if type(x)is not dict or set(x)!={'reference','bound'}:raise ValueError('request needs exactly reference and bound')
    r=validate(x['reference']);m=x['bound'];k=len(r['alphabet'])
    if not integer(m,len(r['transitions']),3 if k==1 else 2) or k>2:raise ValueError('atlas needs unary bound <=3 or binary bound <=2, at least reference size')
    return r,m


def analyze(x):
    r,m=domain(x);x=json.loads(json.dumps(x));r=x['reference'];a=r['alphabet'];k=len(a)
    base=conformance({'reference':r,'implementation':r,'bound':m});words=[t['word']for t in base['tests']];expected=[t['expected']for t in base['tests']];candidates=[]
    for transitions in itertools.product(range(m),repeat=m*k):
        for f in range(1<<m):
            for start in range(m):
                d={'alphabet':a[:],'transitions':[list(transitions[j:j+k])for j in range(0,len(transitions),k)],'start':start,'accept':[q for q in range(m)if f>>q&1]};eq=product(r,d);outputs=[path(d,w)[-1]in d['accept']for w in words];seen={start};queue=[start]
                for q in queue:
                    for z in d['transitions'][q]:
                        if z not in seen:seen.add(z);queue.append(z)
                candidates.append({'id':len(candidates),'machine':d,'reachable_states':len(seen),'counterexample':eq['counterexample'],'outputs':outputs,'rejected_by':[j for j,v in enumerate(outputs)if v!=expected[j]]})
    faults=[c for c in candidates if c['counterexample']is not None];subsets=[]
    for mask in range(1<<len(words)):
        ids=[j for j in range(len(words))if mask>>j&1];miss=[c['id']for c in faults if not any(mask>>j&1 for j in c['rejected_by'])]
        subsets.append({'mask':mask,'tests':ids,'count':len(ids),'symbols':sum(len(words[j])for j in ids),'covered_faults':len(faults)-len(miss),'missed_faults':len(miss),'first_survivor':miss[0]if miss else None})
    complete=[s for s in subsets if not s['missed_faults']];best=min((s['count'],s['symbols'])for s in complete);optimal=[s['mask']for s in complete if(s['count'],s['symbols'])==best];chosen=optimal[0];necessity=[]
    for j in subsets[chosen]['tests']:
        necessity.append({'test':j,'survivor_without':subsets[chosen^(1<<j)]['first_survivor']})
    return {'schema':'dfalab-fault-atlas-v1','request':x,'suite_certificate':base,'words':words,'expected':expected,'candidates':candidates,'subsets':subsets,'optimal_masks':optimal,'chosen_mask':chosen,'chosen_necessity':necessity,'full_suite_essential':[j for j in range(len(words))if subsets[((1<<len(words))-1)^(1<<j)]['missed_faults']>0], 'summary':{'declared_states':m,'candidates':len(candidates),'equivalent':len(candidates)-len(faults),'faults':len(faults),'full_tests':len(words),'subsets_checked':len(subsets),'minimum_tests':best[0],'minimum_symbols_at_minimum_tests':best[1],'optimal_suites':len(optimal)}}


def verify(report):
    try:_verify(report);return True
    except(ValueError,TypeError,KeyError,IndexError,AttributeError,RecursionError):return False


def _verify(c):
    def ok(x):
        if not x:raise ValueError('invalid fault atlas')
    ok(type(c)is dict and set(c)=={'schema','request','suite_certificate','words','expected','candidates','subsets','optimal_masks','chosen_mask','chosen_necessity','full_suite_essential','summary'}and c['schema']=='dfalab-fault-atlas-v1');r,m=domain(c['request']);a=r['alphabet'];k=len(a);base=c['suite_certificate'];ok(verify_conformance(base));ok(same(base['request'],{'reference':r,'implementation':r,'bound':m}));words=[t['word']for t in base['tests']];expected=[t['expected']for t in base['tests']];ok(same(c['words'],words)and same(c['expected'],expected));N=m**(m*k)*(1<<m)*m;ok(type(c['candidates'])is list and len(c['candidates'])==N)
    def run(d,w):
        q=d['start']
        for ch in w:q=d['transitions'][q][a.index(ch)]
        return q in d['accept']
    def shortest(d):
        seen={(r['start'],d['start'])};todo=[(r['start'],d['start'],'')]
        for p,q,w in todo:
            if(p in r['accept'])!=(q in d['accept']):return w
            for j,ch in enumerate(a):
                z=(r['transitions'][p][j],d['transitions'][q][j])
                if z not in seen:seen.add(z);todo.append((*z,w+ch))
        return None
    faults={};rejects={}
    for identifier,t in enumerate(c['candidates']):
        z=identifier;start=z%m;z//=m;f=z%(1<<m);z//=1<<m;flat=[0]*(m*k)
        for j in range(len(flat)-1,-1,-1):flat[j]=z%m;z//=m
        d={'alphabet':a,'transitions':[flat[j*k:(j+1)*k]for j in range(m)],'start':start,'accept':[q for q in range(m)if f&(1<<q)]};seen={start}
        while True:
            nxt=seen|{v for q in seen for v in d['transitions'][q]}
            if nxt==seen:break
            seen=nxt
        ce=shortest(d);out=[run(d,w)for w in words];bad=[j for j in range(len(words))if out[j]!=expected[j]];ok(same(t,{'id':identifier,'machine':d,'reachable_states':len(seen),'counterexample':ce,'outputs':out,'rejected_by':bad}));ok((ce is None)==(not bad));rejects[identifier]=set(bad)
        if ce is not None:faults[identifier]=bad
    ok(type(c['subsets'])is list and len(c['subsets'])==2**len(words));complete=[]
    for mask,s in enumerate(c['subsets']):
        ids=[j for j in range(len(words))if(mask//2**j)%2];miss=[identifier for identifier,bad in faults.items()if not(set(ids)&set(bad))];want={'mask':mask,'tests':ids,'count':len(ids),'symbols':sum(map(len,[words[j]for j in ids])),'covered_faults':len(faults)-len(miss),'missed_faults':len(miss),'first_survivor':miss[0]if miss else None};ok(same(s,want))
        if not miss:complete.append(want)
    best=min((s['count'],s['symbols'])for s in complete);opt=[s['mask']for s in complete if(s['count'],s['symbols'])==best];chosen=opt[0];necessity=[{'test':j,'survivor_without':c['subsets'][chosen-2**j]['first_survivor']}for j in c['subsets'][chosen]['tests']];ess=[j for j in range(len(words))if any(bad==[j]for bad in faults.values())];summary={'declared_states':m,'candidates':N,'equivalent':N-len(faults),'faults':len(faults),'full_tests':len(words),'subsets_checked':2**len(words),'minimum_tests':best[0],'minimum_symbols_at_minimum_tests':best[1],'optimal_suites':len(opt)};ok(same(c['optimal_masks'],opt)and same(c['chosen_mask'],chosen)and same(c['chosen_necessity'],necessity)and same(c['full_suite_essential'],ess)and same(c['summary'],summary));ok(all(v['survivor_without']is not None for v in necessity))


def main():
    from .__main__ import main as cli
    return cli(generator=analyze,verifier=verify,description='Exhaustive tiny DFA fault atlas and exact W-suite subset selection')

if __name__=='__main__':raise SystemExit(main())
