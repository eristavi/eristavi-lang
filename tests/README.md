# Compiler Tests

Compiler tests will live here as the bootstrap implementation begins.

The first tests should cover only settled bootstrap behavior:

- tokenization of `let`, `be`, literals, identifiers, operators, and semicolons;
- parsing variable declarations;
- arithmetic precedence;
- name resolution;
- type inference for basic literals;
- clear diagnostics for unknown names and incompatible operations;
- successful processing of `examples/hello.eri`.

Tests should grow with semantics, not ahead of them.
