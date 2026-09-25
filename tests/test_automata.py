import unittest
from automata import FiniteAutomaton, Transition, EPSILON

class AutomataTests(unittest.TestCase):
    def test_dfa_acceptance(self):
        a = FiniteAutomaton(
            ["q0", "q1"], ["0", "1"],
            [Transition("q0","0","q1"), Transition("q0","1","q0"),
             Transition("q1","0","q1"), Transition("q1","1","q0")],
            "q0", {"q1"}
        )
        self.assertTrue(a.simulate_dfa("0")[0])
        # 01 ends in q0, which is not accepting in this DFA.\n        self.assertFalse(a.simulate_dfa("01")[0])

    def test_nfa_to_dfa(self):
        a = FiniteAutomaton(
            ["q0","q1","q2"], ["0","1"],
            [Transition("q0","0","q0"), Transition("q0","0","q1"),
             Transition("q1","1","q2")],
            "q0", {"q2"}
        )
        dfa = a.to_dfa()
        self.assertFalse(dfa.is_deterministic() is False)
        self.assertTrue(dfa.simulate_dfa("01")[0])

    def test_epsilon_nfa(self):
        a = FiniteAutomaton(
            ["q0","q1"], ["a"],
            [Transition("q0",EPSILON,"q1"), Transition("q1","a","q1")],
            "q0", {"q1"}
        )
        self.assertTrue(a.simulate_nfa("aaa")[0])

if __name__ == "__main__":
    unittest.main()
