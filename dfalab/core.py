"""Classic observation-table L*, exact finite teachers, replayable witnesses.

Algorithm: Dana Angluin, Learning Regular Sets from Queries and Counterexamples
(1987). Original implementation and fixtures, not a new learning algorithm.
"""
from collections import deque
import itertools
import json
import re


def integer(x, lo, hi):
    return type(x) is int and lo <= x <= hi


def validate(d):
    if type(d) is not dict or set(d) != {'alphabet', 'transitions', 'start', 'accept'}:
        raise ValueError('DFA needs exactly alphabet, transitions, start and accept')
    a, ts, f = d['alphabet'], d['transitions'], d['accept']
    if type(a) is not list or not 1 <= len(a) <= 3 or any(type(x) is not str or re.fullmatch('[a-z]', x) is None for x in a) or a != sorted(set(a)):
        raise ValueError('alphabet must contain 1..3 sorted distinct ASCII lowercase letters')
    if type(ts) is not list or not 1 <= len(ts) <= 6:
        raise ValueError('transitions need 1..6 states')
    n = len(ts)
    if any(type(row) is not list or len(row) != len(a) or any(not integer(q, 0, n-1) for q in row) for row in ts):
        raise ValueError('transition rows need one valid state ID per letter')
    if not integer(d['start'], 0, n-1) or type(f) is not list or any(not integer(q, 0, n-1) for q in f) or f != sorted(set(f)):
        raise ValueError('invalid start or accepting state IDs')
    return d


def order(words):
    return sorted(set(words), key=lambda w: (len(w), w))


def path(d, w, start=None):
    q = d['start'] if start is None else start
    out = [q]
    for c in w:
        q = d['transitions'][q][d['alphabet'].index(c)]
        out.append(q)
    return out


def member(d, w):
    return path(d, w)[-1] in d['accept']


def product(left, right):
    """All reachable product pairs in BFS/shortlex access order, not a sample."""
    a = left['alphabet']
    start = (left['start'], right['start'])
    pairs, words, seen = [start], [''], {start: 0}
    edges, mismatch = [], None
    for i, (p, q) in enumerate(pairs):
        if (p in left['accept']) != (q in right['accept']) and mismatch is None:
            mismatch = words[i]
        row = []
        for k, c in enumerate(a):
            nxt = (left['transitions'][p][k], right['transitions'][q][k])
            if nxt not in seen:
                seen[nxt] = len(pairs)
                pairs.append(nxt)
                words.append(words[i] + c)
            row.append(seen[nxt])
        edges.append(row)
    return {'pairs': [list(p) for p in pairs], 'words': words, 'edges': edges,
            'outputs': [[p in left['accept'], q in right['accept']] for p, q in pairs],
            'counterexample': mismatch}


def separation(d, p, q):
    queue = deque([(p, q, '')]); seen = {(p, q)}
    while queue:
        x, y, w = queue.popleft()
        if (x in d['accept']) != (y in d['accept']):
            return w
        for k, c in enumerate(d['alphabet']):
            pair = (d['transitions'][x][k], d['transitions'][y][k])
            if pair not in seen:
                seen.add(pair); queue.append((*pair, w+c))
    return None


def table(d, S, E, cache):
    a = d['alphabet']
    words = order(S + [s+c for s in S for c in a])
    queries = []
    for w in order([s+e for s in words for e in E]):
        if w not in cache:
            ps = path(d, w); cache[w] = ps[-1] in d['accept']
            queries.append({'word': w, 'answer': cache[w], 'path': ps})
    bits = {w: [cache[w+e] for e in E] for w in words}
    closure = [w for w in words if w not in S and bits[w] not in [bits[s] for s in S]]
    consistency = []
    for i, s in enumerate(S):
        for t in S[i+1:]:
            if bits[s] == bits[t]:
                for c in a:
                    diff = [e for k, e in enumerate(E) if bits[s+c][k] != bits[t+c][k]]
                    if diff:
                        consistency.append({'left': s, 'right': t, 'letter': c, 'suffixes': diff})
    return {'S': S[:], 'E': E[:], 'rows': [{'word': w, 'bits': bits[w]} for w in words],
            'queries': queries, 'closure': closure, 'consistency': consistency}, bits


def hypothesis(d, S, E, bits):
    reps, signatures = [], []
    for s in S:
        if bits[s] not in signatures:
            reps.append(s); signatures.append(bits[s])
    h = {'alphabet': d['alphabet'][:],
         'transitions': [[signatures.index(bits[s+c]) for c in d['alphabet']] for s in reps],
         'start': signatures.index(bits['']),
         'accept': [i for i, sig in enumerate(signatures) if sig[E.index('')]]}
    return {'dfa': h, 'representatives': reps}


def minimal(d):
    access = {d['start']: ''}
    queue = [d['start']]
    for q in queue:
        for k, c in enumerate(d['alphabet']):
            r = d['transitions'][q][k]
            if r not in access:
                access[r] = access[q]+c; queue.append(r)
    return {'access': [access[q] for q in range(len(d['transitions']))],
            'distinctions': [{'left': p, 'right': q, 'suffix': separation(d, p, q)}
                             for p in range(len(d['transitions'])) for q in range(p+1, len(d['transitions']))]}


def learn(target):
    validate(target)
    # Copy so the returned certificate never aliases caller input.
    target = json.loads(json.dumps(target))
    S, E, cache, steps = [''], [''], {}, []
    for _ in range(64):
        step, bits = table(target, S, E, cache)
        if step['consistency']:
            w = step['consistency'][0]; new = w['letter']+w['suffixes'][0]
            action = {'kind': 'consistency', 'add': new}
            E = order(E+[new])
        elif step['closure']:
            new = step['closure'][0]; action = {'kind': 'closure', 'add': new}
            S = order(S+[new])
        else:
            h = hypothesis(target, S, E, bits)
            eq = product(target, h['dfa']); w = eq['counterexample']
            action = {'kind': 'conjecture', 'hypothesis': h, 'equivalence': eq}
            if w is not None:
                S = order(S+[w[:k] for k in range(len(w)+1)])
        step['action'] = action; steps.append(step)
        if action['kind'] == 'conjecture' and action['equivalence']['counterexample'] is None:
            final = action['hypothesis']['dfa']
            return {'schema': 'dfalab-learning-v1', 'target': target, 'steps': steps,
                    'final': final, 'minimality': minimal(final),
                    'stats': {'membership_queries': len(cache),
                              'equivalence_queries': sum(s['action']['kind'] == 'conjecture' for s in steps),
                              'closure_repairs': sum(s['action']['kind'] == 'closure' for s in steps),
                              'consistency_repairs': sum(s['action']['kind'] == 'consistency' for s in steps)}}
    raise ValueError('bounded learning trace exceeded 64 steps')


def same(a, b):
    # JSON strictness: bool is not an integer, unknown fields/order are checked.
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if type(a) is list:
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def verify(report):
    """Independent certificate replay. No learner, table or product calls.

    Each table and canonical update is checked from source membership simulation;
    equivalence is rebuilt by a separate shortest-access fixed point. Minimality
    uses exhaustive pair reachability and shortest distinguishing experiments.
    """
    try:
        _verify(report)
        return True
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RecursionError):
        return False


def _verify(r):
    def require(ok):
        if not ok:
            raise ValueError('invalid learning certificate')
    require(type(r) is dict and set(r) == {'schema','target','steps','final','minimality','stats'} and r['schema'] == 'dfalab-learning-v1')
    d = validate(r['target']); alphabet = d['alphabet']; accepting = set(d['accept'])
    def trace(w, machine=d, initial=None):
        q = machine['start'] if initial is None else initial; out = [q]
        for ch in w:
            q = machine['transitions'][q][machine['alphabet'].index(ch)]; out.append(q)
        return out
    def answer(w):
        return trace(w)[-1] in accepting
    def canonical(ws):
        return sorted(set(ws), key=lambda x:(len(x), x))
    def reach(m1,m2,initial):
        # Fixed-point shortest access words, then shortlex order. Independent of
        # generator BFS enumeration, including all edges beyond first mismatch.
        access = {initial:''}
        while True:
            improved = dict(access)
            for (p,q),w in access.items():
                for k,c in enumerate(alphabet):
                    dest = (m1['transitions'][p][k],m2['transitions'][q][k]); v=w+c
                    if dest not in improved or (len(v),v)<(len(improved[dest]),improved[dest]):improved[dest]=v
            if improved == access:break
            access=improved
        pairs=sorted(access,key=lambda z:(len(access[z]),access[z])); ids={p:i for i,p in enumerate(pairs)}
        bad=[access[(p,q)] for p,q in pairs if (p in m1['accept'])!=(q in m2['accept'])]
        return {'pairs':[list(p) for p in pairs],'words':[access[p] for p in pairs],
                'edges':[[ids[(m1['transitions'][p][k],m2['transitions'][q][k])] for k in range(len(alphabet))] for p,q in pairs],
                'outputs':[[p in m1['accept'],q in m2['accept']] for p,q in pairs],
                'counterexample':bad[0] if bad else None}
    require(type(r['steps']) is list and 1<=len(r['steps'])<=64)
    S,E,known=[''],[''],set(); counts={'membership_queries':0,'equivalence_queries':0,'closure_repairs':0,'consistency_repairs':0}; final=None
    for idx,step in enumerate(r['steps']):
        require(type(step) is dict and set(step)=={'S','E','rows','queries','closure','consistency','action'})
        require(same(step['S'],S) and same(step['E'],E))
        ws=canonical(S+[s+c for s in S for c in alphabet]); cols={w:[answer(w+e) for e in E] for w in ws}
        require(same(step['rows'],[{'word':w,'bits':cols[w]} for w in ws]))
        new=canonical([w+e for w in ws for e in E if w+e not in known]);qs=[{'word':w,'answer':answer(w),'path':trace(w)} for w in new]
        require(same(step['queries'],qs)); known.update(new);counts['membership_queries']+=len(new)
        closed=[w for w in ws if w not in S and all(cols[w]!=cols[s] for s in S)]
        inconsistent=[]
        for i,s in enumerate(S):
            for t in S[i+1:]:
                if cols[s]!=cols[t]:continue
                for c in alphabet:
                    es=[e for j,e in enumerate(E) if cols[s+c][j]!=cols[t+c][j]]
                    if es:inconsistent.append({'left':s,'right':t,'letter':c,'suffixes':es})
        require(same(step['closure'],closed) and same(step['consistency'],inconsistent))
        if inconsistent:
            w=inconsistent[0]['letter']+inconsistent[0]['suffixes'][0];require(same(step['action'],{'kind':'consistency','add':w}));E=canonical(E+[w]);counts['consistency_repairs']+=1
        elif closed:
            w=closed[0];require(same(step['action'],{'kind':'closure','add':w}));S=canonical(S+[w]);counts['closure_repairs']+=1
        else:
            representatives=[]
            for s in S:
                if not any(cols[s]==cols[t] for t in representatives):representatives.append(s)
            def state(w):return next(i for i,s in enumerate(representatives) if cols[s]==cols[w])
            h={'alphabet':alphabet[:],'transitions':[[state(s+c) for c in alphabet] for s in representatives],
               'start':state(''),'accept':[i for i,s in enumerate(representatives) if answer(s)]}
            eq=reach(d,h,(d['start'],h['start']))
            expected={'kind':'conjecture','hypothesis':{'dfa':h,'representatives':representatives},'equivalence':eq}
            require(same(step['action'],expected));counts['equivalence_queries']+=1
            w=eq['counterexample']
            if w is None:require(idx==len(r['steps'])-1);final=h
            else:S=canonical(S+[w[:k] for k in range(len(w)+1)])
    require(final is not None and same(r['final'],final) and same(r['stats'],counts))
    rr=reach(final,final,(final['start'],final['start']));access={p[0]:w for p,w in zip(rr['pairs'],rr['words'])}
    require(len(access)==len(final['transitions']))
    distinctions=[]
    for p in range(len(final['transitions'])):
        for q in range(p+1,len(final['transitions'])):
            sep=reach(final,final,(p,q))['counterexample'];require(sep is not None)
            distinctions.append({'left':p,'right':q,'suffix':sep})
    require(same(r['minimality'],{'access':[access[q] for q in range(len(final['transitions']))],'distinctions':distinctions}))
