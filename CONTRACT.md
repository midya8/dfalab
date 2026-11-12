# DFALab learning contract

## Input and finite teacher

A teacher is exactly `{alphabet, transitions, start, accept}`. Alphabet has 1..3 sorted distinct one-character ASCII lowercase letters. Transitions has 1..6 rows with one valid integer state ID per letter, defining a complete deterministic automaton. Start is a valid integer; accept is an increasing unique list of valid integers. Booleans are not IDs. Empty acceptance and unreachable states are valid. The language includes a word exactly when the state reached after the whole word is accepting; rejecting a prefix does not necessarily reject every extension.

Words are strings over the supplied alphabet. The empty string is displayed as ε. Every set of words is ordered shortlex: increasing length, then alphabet order. User state IDs may be nonminimal or unreachable. A minimal learned automaton need not reproduce those IDs or the number of supplied states.

The algorithm uses the teacher through membership and equivalence answers. Teacher-side paths and source transitions support the audit; they do not influence table repair choices beyond those answers. This is not a security boundary. There is no unknown production service, random membership noise or observation reset problem here.

## Classic L* and canonical choices

The implementation follows Angluin's original observation-table learner, including adding **all prefixes** of each counterexample, not a later counterexample-processing variant.

Start S=E={ε}. S is prefix-closed and E suffix-closed. Rows are S union S·A, shortlex ordered. A cell T(s·e) is the teacher's membership answer for row word s and experiment e. Unique membership queries are cached globally and recorded in shortlex order when first needed. A query's path contains the initial state and one reached state per letter.

The report lists every boundary word whose row has no equal S row. It also lists every pair s<t of equal S rows and each letter a for which successor rows differ, together with all distinguishing e in E. Consistency repairs have priority. Select the first listed consistency witness and add a·e for its first e to E. Otherwise select the first closure witness and add it to S. All sets are re-sorted shortlex. These rules preserve suffix and prefix closure.

When both checks pass, distinct S rows become hypothesis states, ordered by their first S representative. The initial row determines the start state, membership at ε determines acceptance, and successor row classes determine transitions. Closedness makes destinations exist; consistency makes them independent of the representative.

The exact teacher computes the **complete reachable product**, with pairs and access words in BFS/shortlex discovery order. It records every pair's outputs and all labeled outgoing pair IDs, including pairs reached after a mismatch. The first output mismatch gives the shortest shortlex counterexample. The empty word can itself be a counterexample. If none exists, the product is a reachable, transition-closed output-agreeing relation, proving language equivalence for every finite word. This is not a bounded test horizon.

Every counterexample and all prefixes are added to S. The process stops only after exact equivalence, never when query scores or a finite sample look good. The implementation has a defensive 64-table bound under the six-state teacher limit. A bound failure is an error, not a success or approximate report.

## Final minimality and scope

The final machine records a shortest access word to every state and a shortest distinguishing suffix for every unordered pair. Reachability and pairwise language distinction prove minimality. State IDs follow the table's representatives, not an isomorphism to the supplied teacher. Minimality does not mean that the learning run used the minimum possible number of queries.

The learner is deterministic for a fixed teacher and the stated ordering. Classic L* and shortest counterexample equivalence are known methods. No new algorithm, scalability result, production security guarantee, real-system inference or general automata learner is claimed. DFA acceptance is only a coarse whole-word protocol language, not outputs, probabilities, timing or safety under all environment behavior.

## Certificate and independent verifier

`dfalab-learning-v1` contains exactly schema, target, steps, final, minimality and stats. Each step contains S, E, rows, queries, closure, consistency and action. Each action is a closure repair, consistency repair or conjecture with its hypothesis and full equivalence product. Stats count unique membership words, conjectures and each repair kind. They are not wall-clock or throughput measures.

The native verifier checks each membership cell through its own direct target simulation, all newly needed queries and paths, every closure and consistency witness, the canonical update and exact hypothesis. It rebuilds product reachability through a separate shortest-access fixed point rather than the generator's queue. It separately checks final access and shortest state-pair distinctions. It does not call the learner, table builder, hypothesis builder, product builder or minimality generator. Exact fields, JSON types, ordering and completeness are checked; an incomplete witness is invalid.

The browser implementation uses string signatures and its own state indexing/query cache. Complete reports are compared against native results and independently verified. Tests use a separate classical pair-marking minimization oracle on the target and on the disjoint union of target/hypothesis, not the observation-table or product algorithms. Shorter counterexample words are independently enumerated in native tests.

CLI generation accepts at most 64 KiB; certificate verification accepts at most 8 MiB. Reads are bounded before allocation. Duplicate decoded JSON keys and nonfinite JSON values are rejected. File output is atomic and invalid input exits 2 without replacing an existing output. Python 3.10+, no runtime dependencies; installed `dfalab` and `python -m dfalab` are checked outside the checkout. Browser teacher JSON is likewise limited to 64 KiB and rejects duplicate decoded keys and decimal/exponent state-ID literals. Probe words are at most 64 letters; invalid probes clear the probe audit. Editing a teacher clears every result and export until a valid rerun.

## Learning controls and validation

Nine synthetic controls defined here include empty/universal languages, parity, delayed acceptance, unreachable acceptance, nonzero start labels, suffix recognition, unary periods and a seeded six-state teacher needing several conjectures and consistency repairs. A closed/consistent conjecture is visibly refuted. Delayed acceptance makes short-prefix agreement particularly misleading. The controls are descriptive examples, not an ablation, performance benchmark or a causal claim about query efficiency.

Native tests enumerate every two-state binary teacher and every three-state unary and binary teacher, including accepting sets and starts. Additional seeded teachers cover up to six states and three letters. Pair-marking references check language equivalence and minimal reachable state counts. Mutation tests reject wrong answers, paths, bits, transitions, pair graphs, stats, missing distinctions and truncated steps. Generator functions are disabled while verification still passes. Browser tests replay all tables at 320/390/1280 pixels, check every query/observation/transition/product row, final access, probes, export, stale clearing and overflow. Installed-wheel checks exercise all controls through both entry points and confirm three site-packages module origins.

## Sources and attribution

These sources support terminology, algorithm semantics and limits, not validation of this implementation. No source code or external dataset was copied. Only synthetic teacher definitions are included. The even/even parity language is the standard example used in Angluin's paper; the transition encoding and all implementation code here are ours. All sources were inspected November 9, 2026.

1. Dana Angluin, *Learning Regular Sets from Queries and Counterexamples*, Information and Computation 75, 87-106 (1987). Primary paper, mirrored university PDF. Sections 1.1-1.2 distinguish the minimally adequate teacher and finite-DFA equivalence; section 2 defines closed/consistent tables, original all-prefix counterexample processing and the minimal-language learning result. High confidence. https://www.tmit.bme.hu/sites/default/files/learningRegSetsFromQueriesAndCounterExamples.pdf
2. DOI record for the original paper: https://doi.org/10.1016/0890-5401(87)90052-6
3. *Lecture 10: Learning a DFA*, university course notes. Secondary explanation of observation-table learning. Context only; the primary paper governs choices. https://santoshv.github.io/2019CS4510/L930_scribed.pdf
4. *Angluin's Algorithm Seminar*, Indian Institute of Science course seminar slides. Secondary table-learning exposition. Context only, no copied fixture or code. https://www.csa.iisc.ac.in/~deepakd/atc-2021/Angluin-Algorithm-Seminar.pdf
5. LearnLib 19.0.0, *ExtensibleLStarDFA*, official API documentation. Explicitly attributes its DFA learner to Angluin and distinguishes learner variants. This project uses none of its code or dependencies. https://learnlib.de/learnlib/maven-site/latest/apidocs/de.learnlib.algorithm.lstar/de/learnlib/algorithm/lstar/dfa/ExtensibleLStarDFA.html
6. LearnLib 19.0.0, *equivalence oracle package*, official documentation. Lists finite-depth, sample-based and randomized test oracles; an oracle label alone does not imply exact all-word equivalence. No such approximation is substituted here. https://learnlib.de/learnlib/maven-site/latest/apidocs/de.learnlib.oracle.equivalence/de/learnlib/oracle/equivalence/package-summary.html
7. AALpy, official project overview. Active automata learning toolbox and explicit choice of an equivalence oracle. Used for ecosystem context, not a claim of implementing AALpy or matching its capabilities. https://des-lab.github.io/AALpy/
