# Automata Simulator

A bilingual desktop application for a Bachelor's Computer Engineering project on Formal Languages and Automata Theory.

## Implemented features

- Visual automaton designer
- Add/remove states
- Set start and accepting states
- Add/remove transitions
- DFA simulation with Run / Step / Reset
- NFA simulation
- Transition table
- Automatic DFA/NFA detection
- NFA → DFA subset construction, including epsilon transitions (ε)
- Visual graph with state/transition highlighting
- Persian / English interface
- Dark desktop UI
- Automated unit tests for the automata engine

## Run on Windows

Use the same Python interpreter where PySide6 is installed:

```powershell
& "C:\Users\mohammadreza\AppData\Local\Programs\Python\Python311\python.exe" -m pip install -r requirements.txt
& "C:\Users\mohammadreza\AppData\Local\Programs\Python\Python311\python.exe" main.py
```

Or, after selecting Python 3.11 as the VS Code interpreter:

```powershell
python main.py
```

Run tests:

```powershell
python -m unittest discover -s tests -v
```

## Project structure

- `main.py` — PySide6 desktop interface
- `automata.py` — DFA/NFA engine and subset construction
- `tests/test_automata.py` — automated tests
- `README_FA.md` — Persian documentation

**Created by Mohammadreza Kazemi — ساخته شده توسط محمدرضا کاظمی**

