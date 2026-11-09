"""Classic bounded W-method conformance suites for complete minimal DFAs.

The DFA construction is P Sigma^{<=m-n+1} W. It is not a new algorithm.
A finite supplied implementation enables a separate exact equivalence audit.
"""
from collections import deque
import itertools
import json
from .core import validate, integer, order, path, product, separation, same


def accesses(d):
    words={d['start']:''};queue=[d['start']]
    for q in queue:
        for k,c in enumerate(d['alphabet']):
            z=d['transitions'][q][k]
            if z not in words:words[z]=words[q]+c;queue.append(z)
    return [{'state':q,'word':words[q]} for q in sorted(words)]


def request(x):
    if type(x) is not dict or set(x)!={'reference','implementation','bound'}:
        raise ValueError('request needs exactly reference, implementation and bound')
    r,i=validate(x['reference']),validate(x['implementation']);n=len(r['transitions'])
    if r['alphabet']!=i['alphabet']:raise ValueError('reference and implementation alphabets must match')
    if not integer(x['bound'],n,6):raise ValueError('bound must be an integer from reference state count through 6')
    if len(accesses(r))!=n:raise ValueError('reference must have every state reachable')
    if any(separation(r,p,q) is None for p in range(n) for q in range(p+1,n)):
        raise ValueError('reference must be minimal: every state pair needs a distinguishing suffix')
    return r,i


def analyze(x):
    request(x);x=json.loads(json.dumps(x));r,i=x['reference'],x['implementation'];n=len(r['transitions'])
    access=accesses(r);P=order([a['word'] for a in access]);pairs=[{'left':p,'right':q,'suffix':separation(r,p,q)} for p in range(n) for q in range(p+1,n)]
    W=order(['']+[v['suffix'] for v in pairs]);depth=x['bound']-n+1
    middle=[''.join(z) for k in range(depth+1) for z in itertools.product(r['alphabet'],repeat=k)]
    # Preserve one canonical factorization per deduplicated test. The complete
    # Cartesian factors are retained, so every required concatenation is audited.
    factorizations={}
    for p in P:
        for v in middle:
            for w in W:factorizations.setdefault(p+v+w,{'access':p,'middle':v,'suffix':w})
    tests=[]
    for word in order(list(factorizations)):
        rp,ip=path(r,word),path(i,word);expected=rp[-1] in r['accept'];actual=ip[-1] in i['accept']
        tests.append({'word':word,'factors':factorizations[word], 'reference_path':rp,'implementation_path':ip,'expected':expected,'actual':actual,'matches':expected==actual})
    failing=[t['word'] for t in tests if not t['matches']];impl_access=accesses(i);bound_holds=len(impl_access)<=x['bound'];eq=product(r,i)
    passed=not failing
    return {'schema':'dfalab-conformance-v1','request':x,'reference_access':access,'pair_distinctions':pairs,'state_cover':P,'characterization':W,'middle_depth':depth,'middle_words':middle,'tests':tests,'implementation_access':impl_access,'equivalence':eq,
            'summary':{'tests':len(tests),'cartesian_products':len(P)*len(middle)*len(W),'total_symbols':sum(len(t['word']) for t in tests),'suite_passed':passed,'first_failure':failing[0] if failing else None,'implementation_reachable_states':len(impl_access),'bound_holds':bound_holds,'bounded_equivalence_certificate':passed and bound_holds,'exact_equivalent':eq['counterexample'] is None,'assessment':'rejected' if failing else 'certified-within-bound' if bound_holds else 'passed-outside-bound'}}


def verify(report):
    """Independent full suite replay. Never calls analyze or generator helpers."""
    try:
        _verify(report);return True
    except (ValueError,TypeError,KeyError,IndexError,AttributeError,RecursionError):return False


def _verify(cert):
    def ok(test):
        if not test:raise ValueError('invalid conformance certificate')
    ok(type(cert) is dict and set(cert)=={'schema','request','reference_access','pair_distinctions','state_cover','characterization','middle_depth','middle_words','tests','implementation_access','equivalence','summary'} and cert['schema']=='dfalab-conformance-v1')
    x=cert['request'];ok(type(x) is dict and set(x)=={'reference','implementation','bound'});r,i=validate(x['reference']),validate(x['implementation']);a=r['alphabet'];n=len(r['transitions']);m=x['bound'];ok(a==i['alphabet'] and integer(m,n,6))
    def run(d,w,start=None):
        q=d['start'] if start is None else start;qs=[q]
        for ch in w:q=d['transitions'][q][d['alphabet'].index(ch)];qs.append(q)
        return qs
    def sorted_words(ws):return sorted(set(ws),key=lambda v:(len(v),v))
    def shortest(d,init):
        # Separate relaxation algorithm for complete product reachability, not
        # the generator's BFS. Exact shortest shortlex access to each pair.
        found={init:''}
        while True:
            new=dict(found)
            for (p,q),w in found.items():
                for k,ch in enumerate(a):
                    z=(d[0]['transitions'][p][k],d[1]['transitions'][q][k]);v=w+ch
                    if z not in new or (len(v),v)<(len(new[z]),new[z]):new[z]=v
            if new==found:return found
            found=new
    def access(d):
        found=shortest((d,d),(d['start'],d['start']));return [{'state':q,'word':found[(q,q)]} for q in range(len(d['transitions'])) if (q,q) in found]
    ra=access(r);ia=access(i);ok(len(ra)==n and same(cert['reference_access'],ra) and same(cert['implementation_access'],ia))
    distinctions=[]
    for p in range(n):
        for q in range(p+1,n):
            found=shortest((r,r),(p,q));ws=sorted_words([w for (u,v),w in found.items() if (u in r['accept'])!=(v in r['accept'])]);ok(bool(ws));distinctions.append({'left':p,'right':q,'suffix':ws[0]})
    P=sorted_words([v['word'] for v in ra]);W=sorted_words(['']+[v['suffix'] for v in distinctions]);depth=m-n+1;mid=['']
    for k in range(1,depth+1):mid.extend(''.join(z) for z in itertools.product(a,repeat=k))
    ok(same(cert['pair_distinctions'],distinctions) and same(cert['state_cover'],P) and same(cert['characterization'],W) and same(cert['middle_depth'],depth) and same(cert['middle_words'],mid))
    # Reconstruct every required test and choose the lexicographically first
    # factor triple by its positions in the declared canonical factor lists.
    sources={}
    for pi,p in enumerate(P):
        for vi,v in enumerate(mid):
            for wi,w in enumerate(W):
                word=p+v+w;key=(pi,vi,wi)
                if word not in sources or key<sources[word][0]:sources[word]=(key,{'access':p,'middle':v,'suffix':w})
    words=sorted_words(sources);ok(type(cert['tests']) is list and len(cert['tests'])==len(words));fail=[]
    for t,w in zip(cert['tests'],words):
        rp,ip=run(r,w),run(i,w);e=rp[-1] in r['accept'];v=ip[-1] in i['accept'];expected={'word':w,'factors':sources[w][1],'reference_path':rp,'implementation_path':ip,'expected':e,'actual':v,'matches':e==v};ok(same(t,expected))
        if e!=v:fail.append(w)
    found=shortest((r,i),(r['start'],i['start']));ps=sorted(found,key=lambda z:(len(found[z]),found[z]));ids={z:k for k,z in enumerate(ps)};bad=[found[z] for z in ps if (z[0] in r['accept'])!=(z[1] in i['accept'])]
    eq={'pairs':[list(z) for z in ps],'words':[found[z] for z in ps],'edges':[[ids[(r['transitions'][p][k],i['transitions'][q][k])] for k in range(len(a))] for p,q in ps],'outputs':[[p in r['accept'],q in i['accept']] for p,q in ps],'counterexample':bad[0] if bad else None};ok(same(cert['equivalence'],eq))
    passed=not fail;holds=len(ia)<=m
    summary={'tests':len(words),'cartesian_products':len(P)*len(mid)*len(W),'total_symbols':sum(map(len,words)),'suite_passed':passed,'first_failure':fail[0] if fail else None,'implementation_reachable_states':len(ia),'bound_holds':holds,'bounded_equivalence_certificate':passed and holds,'exact_equivalent':not bad,'assessment':'rejected' if fail else 'certified-within-bound' if holds else 'passed-outside-bound'}
    ok(same(cert['summary'],summary));ok(not(passed and holds) or not bad)


def main():
    # Reuse the CLI's bounded/atomic transport, not the learning generator.
    from .__main__ import main as cli
    return cli(generator=analyze,verifier=verify,description='Bounded DFA W-method suites and independent conformance checking')

if __name__=='__main__':raise SystemExit(main())
