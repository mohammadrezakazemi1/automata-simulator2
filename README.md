# Automata Simulator — Formal Languages & Automata Lab

A bilingual desktop application for a Bachelor's Computer Engineering project in Formal Languages and Automata Theory, built with Python and PySide6.

Created by Mohammadreza Kazemi — ساخته شده توسط محمدرضا کاظمی

## Final features

### Automata Designer
- Graphical DFA, NFA and epsilon-NFA design
- Separate DFA and NFA editing modes
- Create and drag states
- Start and accepting states
- Arbitrary symbols including 0, 1, a, b and epsilon
- Multiple destinations for the same symbol in NFA
- Determinism protection in DFA mode
- Delete states and exact transitions
- Text import and automatic DFA/NFA detection
- Transition table

### Simulator
- Run, Step, Previous and Reset
- Adjustable step duration from 1 to 60 seconds
- Current-state and exact-path display
- Parallel NFA state tracking
- Correct epsilon closure at simulation start and after each move
- Exact source/symbol/target transition tracking
- Animated parallel and reverse edges

### NFA to DFA
- Real subset construction
- Epsilon-closure support
- Explicit empty subset when required
- Side-by-side source and result graphs
- Movable states and automatic layout
- Detailed DFA report

### Grammar Lab
- CFG validation and classification
- FIRST / FOLLOW
- String parsing and parse tree
- Leftmost derivation
- Left-recursion removal
- Left factoring
- LL(1) table and conflict detection

## Run on Windows

Use Python 3.11:

~~~powershell
py -3.11 -m pip install -r requirements.txt
py -3.11 main.py
~~~

Run tests:

~~~powershell
py -3.11 -m unittest discover -s tests -v
~~~

## Project structure
- main.py — PySide6 UI and controller
- automata.py — DFA/NFA/epsilon-NFA engine
- grammar.py — CFG and LL(1) algorithms
- tests/ — automated regression tests
- .github/workflows/tests.yml — syntax and unit-test CI
- REPORT_FA.md — detailed Persian report

## Revision highlights
- Parallel transitions are rendered independently instead of being collapsed by source and target.
- NFA simulation keeps all possible states rather than inventing a single path.
- Epsilon closure is applied at simulation start and after each input move.
- Exact transitions are stored for reliable visual highlighting.
- Empty-input acceptance is correct for epsilon-NFAs.
- An exact-transition deletion tool was added to the Designer.
- New regression tests cover branching a/b NFAs and epsilon-NFA conversion.

Created by Mohammadreza Kazemi — ساخته شده توسط محمدرضا کاظمی