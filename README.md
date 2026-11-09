# DFALab

**Ask. Conjecture. Find the missing distinction.**

An inspectable implementation of Dana Angluin's classic L* active DFA learning algorithm. A learner asks membership questions, repairs an observation table and proposes machines. An exact finite teacher returns a shortest counterexample until the conjecture accepts the same language. Every experiment and correction is replayable; the final machine has reachability and pair-separation witnesses proving minimality.

[Browser inspector](https://midya8.github.io/dfalab/) | [Exact contract and sources](CONTRACT.md)

## Why this is interesting

A table can be closed and consistent while its conjecture is wrong. Two access words can look like one state until a new suffix separates them. A six-state supplied teacher can describe a one-state language. Finite testing and exact equivalence are different claims.

The browser exposes every table row, every new unique membership query and its teacher-side path, every closure/consistency witness, all proposed machines and the complete reachable product for each equivalence question. Replay the synthetic controls or edit a bounded teacher. Probe the final machine and export the whole certificate.

Native Python and browser JavaScript independently produce the same reports. An independent native verifier replays the certificate without calling the learner, table builder, product builder or minimality generator. A separate pair-marking oracle checks learned state counts and language equivalence.

## Run offline

```bash
python -m unittest discover -s tests -v
npm test                     # Node 22+ and actual Chrome
bash tools/check_wheel.sh     # installed outside-checkout reproduction
python -m http.server 8000 --directory docs
```

Open localhost:8000. No runtime dependencies, model, API key, paid service or private data. The browser needs no network after local assets load.

```bash
python -m dfalab request.json --output learning.json
python -m dfalab learning.json --verify
pip install .
dfalab request.json --output learning.json
```

Example teacher, accepting exactly words with an even number of a's:

```json
{"alphabet":["a","b"],"transitions":[[1,0],[0,1]],"start":0,"accept":[0]}
```

## Evidence and limits

Eight native tests include all 128 two-state binary teachers, all 648 three-state unary teachers and all 17,496 three-state binary teachers, counting every transition table, accepting set and start state. Seeded larger teachers, original controls, forged certificates, disabled-generator verification and CLI size/atomicity checks are separate. Browser/native equality and independent verification cover 189 complete reports. Actual Chrome replays every control table at phone and desktop sizes and audits rows, experiments, transitions, product witnesses, probes, exports and stale-state clearing.

These are original tiny synthetic controls, not real-world protocol benchmarks or a query-efficiency comparison. Bounds: 1..6 states, 1..3 letters, complete deterministic transitions. Exact equivalence works because the finite teacher is supplied. Testing an unknown service does not inherit it. No noisy, timed, probabilistic or nondeterministic teacher is implemented. The learner/teacher separation is a logical interface, not a security isolation mechanism.

The original algorithm and its theoretical result belong to Angluin (1987). This is an original implementation and an explanatory inspector, not a new learning algorithm or an implementation of LearnLib/AALpy.

MIT license. Full attribution and source notes: [CONTRACT.md](CONTRACT.md).
