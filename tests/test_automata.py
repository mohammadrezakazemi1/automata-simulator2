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

    def test_subset_construction_keeps_dead_state(self):
        a = FiniteAutomaton(
            ["q0", "q1"], ["0", "1"],
            [
                Transition("q0", "0", "q0"),
                Transition("q0", "0", "q1"),
                Transition("q1", "0", "q1"),
            ],
            "q0", {"q1"}
        )
        dfa = a.to_dfa()
        self.assertIn("∅", dfa.states)
        self.assertEqual(dfa.destinations("∅", "0"), {"∅"})
        self.assertEqual(dfa.destinations("∅", "1"), {"∅"})
        self.assertTrue(dfa.simulate_dfa("1")[0] is False)

    def test_nfa_with_a_b_branching(self):
        a = FiniteAutomaton(
            ["q0", "q1", "q2"], ["a", "b"],
            [
                Transition("q0", "a", "q0"),
                Transition("q0", "a", "q1"),
                Transition("q0", "b", "q0"),
                Transition("q1", "b", "q2"),
                Transition("q2", "a", "q2"),
                Transition("q2", "b", "q2"),
            ],
            "q0", {"q2"}
        )
        self.assertTrue(a.simulate_nfa("aab")[0])
        self.assertTrue(a.simulate_nfa("bbb")[0] is False)
        self.assertEqual(
            a.transition_tuples({"q0"}, "a"),
            {("q0", "a", "q0"), ("q0", "a", "q1")},
        )

    def test_epsilon_nfa(self):
        a = FiniteAutomaton(
            ["q0","q1"], ["a"],
            [Transition("q0",EPSILON,"q1"), Transition("q1","a","q1")],
            "q0", {"q1"}
        )
        self.assertTrue(a.simulate_nfa("aaa")[0])
        dfa = a.to_dfa()
        self.assertTrue(dfa.is_deterministic())
        self.assertTrue(dfa.simulate_dfa("aaa")[0])

if __name__ == "__main__":
    unittest.main()
