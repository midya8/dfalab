# Bounded conformance: all tests pass, does the claim hold?

[Live inspector](https://midya8.github.io/dfalab/conformance.html). This is an explanatory implementation of the classic W-method of Vasilevskii and Chow, not a new algorithm. It is separate from the unchanged `dfalab-learning-v1` learning certificate and its exact finite teacher.

## Exact domain and theorem

An input has exactly `reference`, `implementation` and `bound`. Both machines use the [original DFA format](CONTRACT.md): 1..6 declared states, 1..3 sorted lowercase letters, complete deterministic transitions, an explicit start and accepting-state set. Alphabets must agree. Every reference state must be reachable and every pair distinguishable. Let its state count be n. The integer bound m must satisfy n <= m <= 6. The implementation may exceed m, deliberately: that makes a broken fault-domain assumption visible instead of rejecting the instructive case.

Every experiment resets both machines to their stated initial state, runs one whole word, then compares acceptance. This is DFA language semantics, not Mealy transition-output trace semantics. The implementation is fixed throughout testing. Reset is exact and reliable in this finite simulator. No claim is made about a real service's reset behavior, determinism or hidden state count.

The governing source is Kocsis and Rot (2025), [*Complete Test Suites for Automata in Monoidal Closed Categories*, Section 2](https://link.springer.com/chapter/10.1007/978-3-031-90897-2_10). Definitions 2.2-2.4 and Corollary 2.7 give the DFA-specific result: for a minimal n-state specification, a state cover P and characterization set W containing epsilon, `P · Σ^{≤k+1} · W` is (n+k)-complete. Here k=m-n. Equivalently, agreeing on every generated word proves language equivalence **within the at-most-m-state implementation fault domain**. Reducing a supplied candidate to its reachable subautomaton preserves its initial-state language, so our check uses reachable states, not irrelevant unreachable declarations.

## Reproducible construction

- P contains a shortest access word for every reference state. Shortlex means increasing length, then alphabet order.
- W contains epsilon and a shortest distinguishing suffix for every unordered reference-state pair, deduplicated in shortlex order. It is a characterization set, not a minimum characterization set.
- Middle words are all words of lengths zero through m-n+1, in shortlex order.
- Every P × middle × W triple is concatenated. Equal test words are deduplicated, then sorted shortlex. The first triple in factor-list iteration order is the canonical factor witness. Every word is run, including epsilon.
- The certificate retains all factor lists, every deduplicated test, the canonical factors, both complete paths and both acceptance values. Counts distinguish Cartesian triples, unique test words and input letters; resets are counted separately. These are descriptive workload counts, not a timing or efficiency benchmark.

## Four distinct claims

1. **Suite passed:** every supplied output agreed on the finite suite. A failing test always refutes equivalence, even if the state bound was wrong.
2. **Bound holds:** the supplied implementation graph has at most m reachable states. This check is possible only because its graph is provided. The suite itself does not infer this bound.
3. **Bounded equivalence certificate:** suite passed AND the reachable-state bound holds, under the stated complete/resettable/fixed deterministic model.
4. **Exact graph audit:** a separate complete exploration of the supplied reference/candidate product checks all reachable pairs, output agreement and transitions. It provides a shortest counterexample or proves equivalence for these two finite graphs, regardless of m. This is not obtained from testing a black box.

A pass outside the bound stays `passed-outside-bound`, even when the separate graph audit happens to show equivalence. A failure is `rejected`; a pass within the bound is `certified-within-bound`. Never promote a test pass into an unrestricted hidden-system proof.

## Controls and verification

Eleven synthetic controls include a universal unary reference whose four-reachable-state candidate first rejects `aaa`: at m=1 the suite is only epsilon and `a`, passes and cannot certify equivalence. At m=4 it detects the fault. Other controls cover a wrong transition, renamed states with a nonzero start, unreachable candidate declarations, an epsilon mismatch, a three-state suffix language, equivalent extra states inside/outside the bound, a ternary depth-six middle family (1,093 words; 6,015 input letters), and a six-state unary reference with 60 factor triples but 11 unique test words. The standard parity language remains credited to Angluin in the original contract; these are not protocol datasets.

`dfalab-conformance-v1` verification independently enumerates all factor combinations and simulates every path. Fixed-point access and pair-distinction checks do not call the generator's access/product/separation helpers. It checks exact keys, types, canonical ordering, shortest witnesses, every product edge/output and every summary field, including the theorem implication. This is an implementation check, not a machine-checked proof of the published theorem.

The six added native tests preserve all eight learning tests. They independently enumerate all 17,496 three-state binary candidates against three references (52,488 reference/candidate cases), compare suite agreement with a separate pair-marking equivalence oracle, verify all controls plus 200 seeded full reports, disable generator helpers during verification, reject forged fields and check strict transport/atomic output. Native tests run on Python 3.10-3.13. Two added Node tests compare 131 full native/browser-engine reports (11 controls + 120 seeded), also independently verified. Actual Chrome at 320/390/1280 px verifies 33 control reports, every 3,444 selected test's canonical factors and paths, 141 probes, all product rows, export and stale-state clearing. Seven Node/Chrome checks include the original learning tests. The installed wheel reproduces both certificate families from outside the checkout through both module and console entry points.

## Run

```bash
python -m dfalab.conformance request.json --output conformance.json
python -m dfalab.conformance conformance.json --verify
pip install .
dfalab-conformance request.json --output conformance.json
dfalab-conformance conformance.json --verify
python -m unittest discover -s tests -v
npm test
bash tools/check_wheel.sh
```

Generation reads at most 64 KiB; verification at most 8 MiB. Duplicate JSON keys, nonfinite values and excessive nesting are rejected. Browser numeric literals also reject decimal/exponent forms instead of silently accepting them as integer bounds. Output files replace atomically only after successful generation. Size limits bound input transport, not a universal resource guarantee for arbitrary future extensions.

## Background and convention notes

- [Kocsis and Rot, FoSSaCS 2025, Section 2](https://link.springer.com/chapter/10.1007/978-3-031-90897-2_10): primary authority for the precise DFA acceptance theorem and epsilon conventions used here.
- [Angelo Gargantini, *Conformance Testing*](https://cs.unibg.it/gargantini/research/papers/motres05.pdf), Sections 4.2 and 4.4.1: finite-state test assumptions, reset, separating sequences and classic W-method background. Its Mealy presentation uses transition-output traces and different cover naming; we do not copy those formulas into a DFA claim.
- [Huang and Peleska, test automation paper](https://www.informatik.uni-bremen.de/agbs/jp/papers/test-automation-huang-peleska.pdf): background on finite-state testing, not the governing DFA theorem.
- [Aditya P. Mathur, *Foundations of Software Testing*, sample FSM chapter](https://www.cs.purdue.edu/homes/apm/foundationsBook/samples/fsm-chapter.pdf): textbook finite-state test-generation context, not a claim about this implementation's efficiency.
- [Oxford DFA learning notes](https://www.cs.ox.ac.uk/people/james.worrell/DFA-learning.pdf): DFA learning context. The original learning and exact-equivalence interface remains separate.
- [LearnLib equivalence-oracle documentation](https://learnlib.de/learnlib/maven-site/latest/apidocs/de.learnlib.oracle.equivalence/de/learnlib/oracle/equivalence/package-summary.html): existing W-method and random-W-method oracle families. DFALab is not LearnLib and does not implement all its variants.

No minimum-suite, optimal query count, production-protocol coverage, unknown-service bound inference, noisy/timed/probabilistic/nondeterministic testing, or security-isolation claim.
