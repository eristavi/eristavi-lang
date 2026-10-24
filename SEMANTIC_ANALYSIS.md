# Eristavi-written semantic analysis

The compiled frontend now includes an **experimental semantic analyzer written in
Eristavi**. It resolves source modules, names and types, checks safety contracts,
and records expression type/effect facts. Stage-0 remains the trusted reference;
this milestone does not replace the normal compiler or generate application code.

## Build and use

```sh
erist build src/frontend.eri --source-root src -o erist-frontend
./erist-frontend analyze application.eri
./erist-frontend analyze project/src/application.eri --source-root project/src
./erist-frontend analyze-report project/src/application.eri --source-root project/src
```

`analyze` succeeds silently with exit status zero. Invalid source produces a
source-located diagnostic on stderr and exit status one. Incorrect command usage
has status two. `analyze-report` writes an inspection report to stdout on success.
Neither command executes entry statements or creates program output files.

The default source root is the entry file's parent directory. An explicit source
root is canonicalized together with the entry path; the entry must resolve inside
that root. Source module paths are resolved from the root, not the importing
file's directory. Cycles, unresolved modules, duplicate import aliases, private
API access and executable statements in imported modules are rejected. The source
loader is verified on the hosted Linux/macOS matrix and currently uses POSIX path
separators. Interface-only JSON objects remain a Stage-0 facility.

The built executable needs no Python, C compiler or network access at runtime.
Building it still requires Stage-0, its pinned dependencies and a hosted C toolchain.
The runtime boundary consists of existing file/process/Unicode library operations;
semantic judgments are made by Eristavi source, not delegated to Python or C.

## Implementation

| Module | Responsibility |
| --- | --- |
| `semantic_model.eri` | Explicit identity records for types, symbols, modules, declarations, locations and expression facts. |
| `semantic_types.eri` | Unification, occurs checks, inferred operation constraints, relationship-preserving cloning and unresolved-variable checks. |
| `semantic.eri` | Declaration collection, lexical scopes, typing, inference, presence checks, mutation, failures and resource checks. |
| `semantic_project.eri` | Source module loading, canonical root validation, caching and import-cycle detection. |
| `semantic_report.eri` | Versioned inspection of inferred function contracts. |

The implementation stays inside the frozen source language. There are no explicit
generic parameters, hidden references, structural field guessing, dynamic type
fallbacks, new keywords or alternate declaration forms.

The checked surface includes:

- declaration ordering, forward function/type references and module visibility;
- declaration-before-use, duplicate names and no local/parameter shadowing;
- Int/Float/Bool/Text, signed-64-bit literal range and Bool-only conditions;
- inferred function/collection relationships and explicit recursive result contracts;
- ordinary nominal values, field construction, Lists and explicit Text views;
- `maybe` presence checks on local bindings and explicit `identity` values;
- transitive `fixed`, writable paths and ordinary-value equality requirements;
- return/completion consistency and no-value expression restrictions;
- typed checked failures, `try`, ordered handlers and complete handling;
- scoped resource acquisition, cleanup-failure contracts and rejection of ordinary
  copying/escape through returns, arguments, assignments, Lists and value fields.

Generic templates retain shared parameter/result relationships. Type variables
carry inferred operation, equality and deep-fixed requirements; call-site cloning
preserves those relationships. Explicit identity is used only in the compiler's
own data structures, according to the same rules as ordinary Eristavi programs.

## Inspection report

The report has format `eristavi-semantics-v1`, `experimental: true`, an array of
function contracts, and an `expressionFacts` count. Each function reports its
parameter relationships, result type and checked failures. Internal variables use
names such as `T0` for explanation; these are not source syntax. Shape and operation
constraints are compared against Stage-0's inferred type data.

The report is an inspection contract, not the production module-interface/object
format or a new public IR. Expression facts are retained in the analyzed module
model for the later IR implementation; they do not yet constitute code generation.

## Conformance evidence

`tests/fixtures/semantic_cases.json` freezes **175 cases: 67 accepted, 108 rejected**.
The same projects are checked independently by Stage-0 and the compiled analyzer.
Tests compare acceptance, diagnostic phase/location/category, and inferred function
contracts across accepted cases. Multi-file cases cover visibility, generic API
relationships, checked errors, dependency caching and cycles.

There are **10 intentional location differences** recorded with a reason in the
fixture. Generic instantiation failures point at the call site rather than the
reference's reanalyzed function body. A duplicate import qualifier points at the
conflicting import rather than an earlier reference alias-table failure. These
are diagnostic differences, not different acceptance rules in this corpus.

The analyzer checks the frontend's own source module graph with an empty `PATH`.
Selected programs also run through the reference interpreter executing the same
Eristavi analyzer, and their diagnostics/status are compared to compiled execution.
Passing this corpus is evidence of the covered surface, not proof of complete
semantic equivalence for every possible program. The candidate stays opt-in.

Conformance exposed and corrected Stage-0 implementation defects without changing
the specification: duplicate parameter acceptance, treating ordinary fields named
`count` as read-only List properties, resource copies into ordinary storage, and
no-value List elements. These corrections enforce the existing no-shadowing,
ordinary-value and single-owner resource contracts.

## Next promotion gates

Continue extending differential coverage, then port typed/source-close IR generation
and verification to consume this analysis. Eristavi-written code generation and a
repeatable self-build follow. Python remains Stage-0 until those gates are met.
A fully standalone native toolchain must additionally own or bundle its assembler
and linker; this frontend milestone does not remove that requirement.
