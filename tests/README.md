# Compiler Tests

The bootstrap test suite is split across:

- `test_bootstrap.py` — source-language frontend and AST execution runtime;
- `test_project.py` — multi-file module/import behavior;
- `test_backend.py` — typed IR → C → native executable path.

Run everything from the repository root:

```text
python -m unittest discover -s tests -v
```

The current suite contains **80 tests**.

Coverage includes lexical fundamentals, checked scalar arithmetic, type annotations, scope/no-shadowing, control flow, function result inference and recursion, compiler-inferred generic relationships, Lists, user-defined values and construction, maybe/none narrowing, identity, checked errors and propagation, deterministic file-resource use, project imports/visibility/cycles, and the first C/native backend.

Backend tests compile and execute generated C when a system `cc` is available, including checked Int overflow, recursion, loops, Text equality/escaping, and Unicode source identifiers.

Tests should continue to grow with implemented frozen semantics and cross-backend conformance rather than speculative future syntax.
