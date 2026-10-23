# Compiler Tests

The bootstrap test suite now lives in `tests/test_bootstrap.py`.

Run it from the repository root with:

```text
python -m unittest discover -s tests -v
```

The first suite intentionally covers only frozen behavior already implemented by the vertical bootstrap slice:

- execution of the canonical hello program;
- rejection of reassignment to `fixed` bindings;
- no implicit `Int` / `Float` mixing;
- rejection of `%` for Float;
- truncation-compatible signed Int remainder;
- nested block comments;
- locked Boolean/comparison precedence.

Tests should continue to grow with implemented frozen semantics, not speculative future features.
