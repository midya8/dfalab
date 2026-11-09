# Finite fault atlas: every tiny implementation and every W-suite subset

[Live atlas](https://midya8.github.io/dfalab/fault-atlas.html). This extends [bounded conformance](CONFORMANCE.md), not the original L* learning schema. Classic W-method and set-cover ideas are credited below. This is an original implementation and inspector, not a new test-generation algorithm.

## Precise question

For a supplied minimal reachable reference and a tiny complete implementation domain, which **subset of the constructed W-suite** rejects every nonequivalent candidate? The objective is lexicographic: minimize number of independent tests (one reset per word), then total input letters among minimum-count subsets. All tied optimal masks are retained, in numeric order. The lowest numeric mask is the deterministic displayed choice, not a mathematical preference.

No arbitrary new test words are searched. No prefix-sharing discount or Mealy prefix-output observation is used. This is not a globally shortest complete test suite, a production-protocol benchmark, a greedy approximation or a new theorem.

## Domain and complete enumeration

Input has exactly `reference` and `bound`. The reference uses the original complete DFA format and must be minimal and reachable. Unary alphabets allow integer m from n through 3; binary alphabets allow m from n through 2. No other alphabets are accepted. The candidate domain contains every complete machine with **exactly m declared states**, including all transition functions, accepting sets and initial states.

For alphabet size k, the labeled candidate count is `m^(m*k) · 2^m · m`: 128 at binary m=2; 648 at unary m=3. Every machine with fewer than m reachable states has an equivalent representative here by adding unreachable states. The implementation-state fault domain therefore covers all initial-state languages realizable with at most m states, despite enumerating exactly m declarations. Unreachable declarations and renamed states create duplicate behaviors. Counts are labeled machines, not distinct languages, independent bugs, probabilities or real-world frequency estimates.

Candidates are ordered by lexicographic flattened transition table, accepting bit mask from zero upward, then start state from zero upward. IDs are zero-based positions in that enumeration. The native generator uses Cartesian enumeration; the verifier independently decodes IDs in mixed radix and checks that every graph, accepting set and start is exactly the required one. No sampling, one-edit mutation restriction or isomorphism filtering is applied.

Every candidate is compared with the reference by exact reachable-product language equivalence. Its shortest shortlex distinguishing word, reachable-state count and acceptance on every full-suite word are retained. An equivalent candidate is **not a fault** and is excluded from the coverage denominator. All non-equivalent candidates must be rejected by the full W-suite; both verifier and tests check this invariant.

## Suite construction, optimization and witnesses

The underlying `dfalab-conformance-v1` certificate uses the reference itself as its supplied implementation and the chosen bound m. Its P, middle and W sets are constructed exactly as [CONFORMANCE.md](CONFORMANCE.md) specifies. The atlas uses the deduplicated words from this certificate, retaining it in full.

For each word, the rejection set contains exactly the candidate IDs whose final acceptance disagrees. A selected subset covers the finite fault domain when the union of its rejection sets includes every non-equivalent candidate. This is finite set cover on behavioral faults, not structural state/transition coverage.

Every mask from zero through `2^t-1` is checked, where t is the full-suite word count. Bit j selects word j in shortlex order. Each row records indices, test count, letter count, faults rejected, faults missed and first escaping non-equivalent candidate. Empty subset is included. All exact minima under the stated objective are retained. Bounds keep exhaustive enumeration small; no polynomial-time or industrial-scale claim is made.

Two different necessity notions remain distinct:

- `full_suite_essential`: omitting a word from the **full** suite allows a fault to escape; equivalently, some fault is rejected only by that word among the full suite.
- `chosen_necessity`: for each word in the displayed **optimal subset**, the earliest fault escaping after removing it. These witnesses prove that subset is irredundant. They alone do not prove cardinality optimality; exhaustive comparison with every subset does.

The browser lets the reader choose every subset, toggle individual bits, jump to the first escaping fault, inspect every candidate graph and read every full-suite acceptance/path row. Correct survivors and escaping faults have different labels. Export includes all candidates, all subsets, all minima, deletion witnesses and the underlying suite certificate. Editing a request clears every old public report/selection and disables stale export.

## Controls and tested counts

Eight synthetic references cover a universal binary language, parity binary language, unary reject-all, unary parity, unary modulo three, a renamed binary reference with a nonzero start and both accepting/rejecting one-state edge cases. Standard parity-language use is not a new language or algorithm.

For the universal binary reference at m=2, exactly 40 of 128 labeled candidates are equivalent and 88 are faults. The seven-word W-suite reduces to epsilon, `a`, `b` under the stated objective: three resets and two letters. This is a result for this explicitly enumerated domain, not a general reduction rate. For unary modulo three at m=3, six of 648 candidates are equivalent. No benchmark or causal mechanism claim is attached to these examples.

Four added native tests preserve all fourteen previous tests. They verify all eight full atlases, cross-check candidate equivalence with an independent pair-marking oracle, and cover **all 60 minimal reachable one/two-state unary or binary references** at their maximum allowed implementation bound. The count is 4 one-state references, 8 two-state unary references and 48 two-state binary references, including all starts and accepting choices. Forged graph/matrix/subset/optimality/witness fields are rejected; verification still works with generator/conformance-construction/product/path helpers disabled. CLI cap/atomic output checks remain active.

Two added Node checks compare eleven complete native/browser-engine atlases (eight controls plus smaller-bound variants), independently verified natively. Actual Chrome runs every control at 320/390/1280 pixels: 24 full reports, **6,996 candidate selections and 804 subset selections**, with graph/matrix paths, equivalent/fault labels, toggles, escaping-witness navigation, export and stale-state checks. The ten Node/Chrome checks include all seven previous checks. All eighteen native tests run on Python 3.10-3.13. Version 0.3.0 installs outside the checkout and reproduces all three certificate families through module and console generation/verification.

## Offline use

```bash
python -m dfalab.fault_atlas request.json --output atlas.json
python -m dfalab.fault_atlas atlas.json --verify
pip install .
dfalab-fault-atlas request.json --output atlas.json
dfalab-fault-atlas atlas.json --verify
python -m unittest discover -s tests -v
npm test
bash tools/check_wheel.sh
```

Example request:

```json
{"reference":{"alphabet":["a","b"],"transitions":[[0,0]],"start":0,"accept":[0]},"bound":2}
```

The strict atomic CLI transport is reused: 64 KiB generation request, 8 MiB verification input, duplicate keys/nonfinite values/excessive nesting rejected. Browser input also rejects decimal/exponent numeric forms for integer fields. No dependency, paid API, model or private data is needed.

## Sources and convention limits

1. [Kocsis and Rot, *Complete Test Suites for Automata in Monoidal Closed Categories*, FoSSaCS 2025, Section 2](https://link.springer.com/chapter/10.1007/978-3-031-90897-2_10): precise DFA W-method theorem used by the underlying suite, credited to Vasilevskii and Chow. No change to its assumptions is inferred from optimization.
2. [Burdonov, Kossatchev and Yevtushenko, *Deriving complete finite tests based on state machines*](https://www.ispras.ru/en/publications/deriving_complete_finite_tests_based_on_state_machines.pdf): finite fault domains and completeness relative to specification, domain and conformance relation. Its wider state-machine results are not implemented here.
3. [*An Empirical Study of Greedy Test Suite Minimization Techniques Using Mutation Coverage*](https://tugraz.elsevierpure.com/ws/portalfiles/portal/70135366/An_Empirical_Study_of_Greedy_Test_Suite_Minimization_Techniques_Using_Mutation_Coverage.pdf): test reduction as set cover, mutation matrices and equivalent-mutant caveats. We use exhaustive subsets, not its greedy algorithms or empirical result claims; our candidates are all graphs, not program mutants.
4. [Mathur, *Foundations of Software Testing*, FSM sample chapter](https://www.cs.purdue.edu/homes/apm/foundationsBook/samples/fsm-chapter.pdf): FSM fault-model and W/Wp background. No textbook test-cost formula is substituted for our explicitly reset-per-word objective.
5. [Gargantini, *Conformance Testing*, Sections 4.2 and 4.4.1](https://cs.unibg.it/gargantini/research/papers/motres05.pdf): reliable reset, fixed complete machines and characterization sets. Its Mealy output-trace conventions differ from our DFA whole-word acceptance.
6. [LearnLib equivalence-oracle API](https://learnlib.de/learnlib/maven-site/latest/apidocs/de.learnlib.oracle.equivalence/de/learnlib/oracle/equivalence/package-summary.html): existing W-method/random-W-method variants and attribution. DFALab is not LearnLib.

All scope and optimality claims here are about supplied finite complete deterministic automata with reliable reset and a fixed implementation. They do not establish a hidden service's model or bound.
