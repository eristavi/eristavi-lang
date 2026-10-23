# Compiler Tests

The bootstrap test suite lives in `tests/test_bootstrap.py`.

Run it from the repository root with:

```text
python -m unittest discover -s tests -v
```

The current 16-test suite covers frozen behavior already implemented by the vertical bootstrap slices:

- execution of the canonical hello program;
- rejection of reassignment to `fixed` bindings;
- no implicit `Int` / `Float` mixing;
- rejection of `%` for Float;
- truncation-compatible signed Int remainder;
- nested block comments;
- locked Boolean/comparison precedence;
- explicit `Int`, `Float`, `Bool`, and `Text` binding annotations;
- rejection of annotation/initializer type mismatches;
- `if` / `else` branch execution;
- Bool-only `if` conditions;
- lexical block-local bindings that do not leak;
- rejection of nested local shadowing;
- assignment to visible outer bindings from nested blocks;
- `while` execution and reassignment;
- legal reuse of a local name in separate sibling scopes.

Tests should continue to grow with implemented frozen semantics, not speculative future features.
