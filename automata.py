"""Core finite-automaton algorithms.

This module contains no GUI code. Keeping the model and algorithms independent
from PySide6 makes the project easier to test and explain academically.
"""

from collections import deque
from dataclasses import dataclass
from typing import FrozenSet, List, Set, Tuple


EPSILON = "ε"


@dataclass(frozen=True)
class Transition:
    """A single automaton transition with an optional numeric weight."""

    source: str
    symbol: str
    target: str
    weight: float = 1.0


class FiniteAutomaton:
    """Representation and algorithms for DFA, NFA and ε-NFA machines."""

    def __init__(
        self,
        states=None,
        alphabet=None,
        transitions=None,
        start=None,
        finals=None,
    ):
        self.states: List[str] = list(dict.fromkeys(states or []))
        self.alphabet: List[str] = list(dict.fromkeys(alphabet or []))
        self.transitions: List[Transition] = list(transitions or [])
        self.start = start
        self.finals: Set[str] = set(finals or [])

    def add_state(self, name: str, final=False):
        """Add a state if it does not already exist."""
        name = name.strip()
        if not name:
            raise ValueError("State name cannot be empty.")
        if name not in self.states:
            self.states.append(name)
        if final:
            self.finals.add(name)
        return name

    def remove_state(self, name: str):
        """Remove a state and every transition connected to it."""
        self.states = [state for state in self.states if state != name]
        self.transitions = [
            transition for transition in self.transitions
            if transition.source != name and transition.target != name
        ]
        self.finals.discard(name)
        if self.start == name:
            self.start = self.states[0] if self.states else None

    def add_transition(self, source: str, symbol: str, target: str, weight: float = 1.0):
        """Add a transition, register its symbol, and store its numeric weight."""
        source, symbol, target = (
            source.strip(),
            symbol.strip(),
            target.strip(),
        )

        if source not in self.states or target not in self.states:
            raise ValueError("Source and target states must exist.")
        if not symbol:
            raise ValueError("Transition symbol cannot be empty.")

        if symbol != EPSILON and symbol not in self.alphabet:
            self.alphabet.append(symbol)

        try:
            weight = float(weight)
        except (TypeError, ValueError):
            raise ValueError("Transition weight must be numeric.")
        if weight < 0:
            raise ValueError("Transition weight cannot be negative.")

        transition = Transition(source, symbol, target, weight)
        if transition not in self.transitions:
            self.transitions.append(transition)

    def destinations(self, source: str, symbol: str) -> Set[str]:
        """Return every state reachable by one transition."""
        return {
            transition.target
            for transition in self.transitions
            if transition.source == source and transition.symbol == symbol
        }

    def is_deterministic(self) -> bool:
        """Check the defining transition constraints of a DFA."""
        seen = set()

        for transition in self.transitions:
            if transition.symbol == EPSILON:
                return False

            key = (transition.source, transition.symbol)
            if key in seen:
                return False
            seen.add(key)

        return True

    def validate(self):
        """Validate the structural invariants required for simulation."""
        if not self.states:
            raise ValueError("Add at least one state.")
        if self.start not in self.states:
            raise ValueError("Select a valid start state.")
        if not self.finals.issubset(set(self.states)):
            raise ValueError("Final states must exist in the state set.")

        for transition in self.transitions:
            if (
                transition.source not in self.states
                or transition.target not in self.states
            ):
                raise ValueError("A transition references a missing state.")

    def step_dfa(self, state: str, symbol: str) -> str:
        """Perform exactly one DFA transition."""
        targets = self.destinations(state, symbol)
        if len(targets) != 1:
            raise ValueError(
                f"DFA transition is not unique for ({state}, {symbol})."
            )
        return next(iter(targets))

    def simulate_dfa(self, text: str) -> Tuple[bool, List[str]]:
        """Simulate a DFA and return (accepted, visited_states)."""
        self.validate()
        if not self.is_deterministic():
            raise ValueError("The current automaton is not deterministic.")

        state = self.start
        path = [state]

        for symbol in text:
            if symbol not in self.alphabet:
                raise ValueError(f"Symbol '{symbol}' is not in the alphabet.")
            state = self.step_dfa(state, symbol)
            path.append(state)

        return state in self.finals, path

    def epsilon_closure(self, states: Set[str]) -> Set[str]:
        """Compute the ε-closure with depth-first graph traversal."""
        closure = set(states)
        stack = list(states)

        while stack:
            current = stack.pop()
            for target in self.destinations(current, EPSILON):
                if target not in closure:
                    closure.add(target)
                    stack.append(target)

        return closure

    def move(self, states: Set[str], symbol: str) -> Set[str]:
        """Move a set of states through one input symbol."""
        return {
            transition.target
            for transition in self.transitions
            if transition.source in states and transition.symbol == symbol
        }

    def simulate_nfa(self, text: str) -> Tuple[bool, List[Set[str]]]:
        """Simulate an NFA/ε-NFA as a sequence of possible-state sets."""
        self.validate()

        current = self.epsilon_closure({self.start})
        path = [set(current)]

        for symbol in text:
            if symbol not in self.alphabet:
                raise ValueError(f"Symbol '{symbol}' is not in the alphabet.")

            current = self.epsilon_closure(self.move(current, symbol))
            path.append(set(current))

        return bool(current & self.finals), path

    def to_dfa(self):
        """Convert an NFA/ε-NFA to a DFA using subset construction."""
        self.validate()
        if self.is_deterministic():
            return self

        start_subset = frozenset(self.epsilon_closure({self.start}))
        names = {start_subset: self._subset_name(start_subset)}

        queue = deque([start_subset])
        dfa_states = [names[start_subset]]
        dfa_transitions = []
        dfa_finals = set()

        while queue:
            subset = queue.popleft()
            state_name = names[subset]

            # A DFA subset is accepting if it contains an NFA final state.
            if set(subset) & self.finals:
                dfa_finals.add(state_name)

            for symbol in self.alphabet:
                target_subset = frozenset(
                    self.epsilon_closure(
                        self.move(set(subset), symbol)
                    )
                )

                # The visualizer omits the empty/dead subset.
                if not target_subset:
                    continue

                if target_subset not in names:
                    names[target_subset] = self._subset_name(target_subset)
                    dfa_states.append(names[target_subset])
                    queue.append(target_subset)

                dfa_transitions.append(
                    Transition(
                        state_name,
                        symbol,
                        names[target_subset],
                    )
                )

        return FiniteAutomaton(
            states=dfa_states,
            alphabet=list(self.alphabet),
            transitions=dfa_transitions,
            start=names[start_subset],
            finals=dfa_finals,
        )

    @staticmethod
    def _subset_name(subset: FrozenSet[str]) -> str:
        """Convert an NFA state subset into a readable DFA state name."""
        if not subset:
            return "∅"
        return "{" + ",".join(sorted(subset)) + "}"

    def clone(self):
        """Return a fully independent copy of the automaton."""
        return FiniteAutomaton(
            states=self.states[:],
            alphabet=self.alphabet[:],
            transitions=[
                Transition(t.source, t.symbol, t.target, t.weight)
                for t in self.transitions
            ],
            start=self.start,
            finals=set(self.finals),
        )
