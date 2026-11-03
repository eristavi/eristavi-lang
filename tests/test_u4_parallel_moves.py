"""Independent simultaneous-assignment oracle for private U4 reference planner."""
import itertools
import unittest
from compiler.erist.u4_parallel_moves import plan_parallel_moves

def execute(plan, state):
    result = dict(state)
    for dst, src in plan:
        result[dst] = result[src]
    return result

class U4ParallelMoveTests(unittest.TestCase):
    def test_cycles_and_acyclic_chains(self):
        for assignments in (
            (("a", "b"), ("b", "a")),
            (("a", "b"), ("b", "c"), ("c", "a")),
            (("a", "b"), ("b", "c")),
            (("a", "b"), ("c", "d"), ("d", "c")),
            (("a", "a"),),
        ):
            original = {key: i for i, key in enumerate(("a", "b", "c", "d", "tmp"))}
            result = execute(plan_parallel_moves(assignments, "tmp"), original)
            for dst, src in assignments:
                self.assertEqual(result[dst], original[src])

    def test_exhaustive_small_permutations(self):
        keys = ("a", "b", "c", "d")
        original = {key: i for i, key in enumerate(keys + ("tmp",))}
        for count in range(1, 5):
            for destinations in itertools.combinations(keys, count):
                for sources in itertools.product(keys, repeat=count):
                    assignments = tuple(zip(destinations, sources))
                    result = execute(plan_parallel_moves(assignments, "tmp"), original)
                    for dst, src in assignments:
                        self.assertEqual(result[dst], original[src])

    def test_reject_alias_and_duplicates(self):
        with self.assertRaises(ValueError):
            plan_parallel_moves((("a", "b"),), "b")
        with self.assertRaises(ValueError):
            plan_parallel_moves((("a", "b"), ("a", "c")), "tmp")

if __name__ == "__main__":
    unittest.main()
