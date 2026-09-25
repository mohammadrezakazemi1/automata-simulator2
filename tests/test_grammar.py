import unittest
from grammar import ContextFreeGrammar

class GrammarTests(unittest.TestCase):
    def test_first_follow(self):
        g=ContextFreeGrammar().parse("S -> a A\nA -> b A | ε")
        self.assertEqual(g.first_sets()["S"], {"a"})
        self.assertIn("$", g.follow_sets()["S"])
        self.assertIn("$", g.follow_sets()["A"])

    def test_parse_string_and_tree(self):
        g=ContextFreeGrammar().parse("S -> a A\nA -> b A | ε")
        ok, tree, tokens = g.parse_string("abb")
        self.assertTrue(ok)
        self.assertEqual(tokens, ["a","b","b"])
        self.assertIsNotNone(tree)

    def test_reject_string(self):
        g=ContextFreeGrammar().parse("S -> a A\nA -> b A | ε")
        ok, _, _ = g.parse_string("aba")
        self.assertFalse(ok)

    def test_left_recursion(self):
        g=ContextFreeGrammar().parse("E -> E + T | T\nT -> id")
        g.remove_left_recursion()
        self.assertFalse(any(p.right and p.right[0] == p.left for p in g.productions))

    def test_ll1_table(self):
        g=ContextFreeGrammar().parse("S -> a A | b B\nA -> c\nB -> d")
        table, conflicts = g.ll1_table()
        self.assertFalse(conflicts)
        self.assertIn(("S","a"), table)

    def test_ll1_conflict(self):
        g=ContextFreeGrammar().parse("S -> a A | a B\nA -> c\nB -> d")
        _, conflicts = g.ll1_table()
        self.assertTrue(conflicts)

    def test_left_factoring(self):
        g=ContextFreeGrammar().parse("S -> a A | a B\nA -> c\nB -> d")
        g.left_factor()
        self.assertTrue(any(p.left.startswith("S") and p.right == ("a","SF") for p in g.productions))

if __name__ == "__main__":
    unittest.main()
