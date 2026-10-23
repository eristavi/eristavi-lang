# Compiler Tests

The bootstrap test suite lives in `tests/test_bootstrap.py`.

Run it from the repository root with:

```text
python -m unittest discover -s tests -v
```

The current 37-test suite covers frozen behavior already implemented by the vertical bootstrap slices:

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
- legal reuse of a local name in separate sibling scopes;
- explicit and inferred function result contracts;
- no-value function execution and bare `return;`;
- rejection of no-value calls in value contexts;
- full successful-path return checking for value-producing functions;
- rejection of incompatible inferred return types;
- rejection of bare return in value-producing functions;
- direct recursion with an explicit result contract;
- rejection of circular direct and mutual result inference;
- order-independent and forward function resolution;
- recursive no-value functions without a result contract;
- duplicate-parameter rejection;
- parameter no-shadowing;
- mutable local parameter values that preserve caller-owned bindings;
- argument type and arity checking;
- module declarations before entry executable statements;
- rejection of top-level `return`.

Tests should continue to grow with implemented frozen semantics, not speculative future features.
