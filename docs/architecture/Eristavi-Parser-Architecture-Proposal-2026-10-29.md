# Eristavi parser architecture — agreed design
Date: 2026-10-29
Status: Architecture and acceptance criteria agreed on 2026-10-29. Implementation and validation have not started.
Scope: Parser and syntax AST internals. Preserve Eristavi source language, the agreed lexer contract, and mandatory downstream semantic/IR verification.

## Recommendation
Use a hand-written predictive recursive-descent parser for declarations, statements, types, and structural forms; use a grammar-exact, fixed-precedence expression parser with explicit tiers. Construct a compact per-module AST directly in append-only indexed storage. Use typed 32-bit IDs, pooled child lists, compilation-scoped SymbolIds, and source spans independent of tokens. Return a complete immutable AST or a structured error.

This is the recommended balance of runtime cost, auditability, and correctness for Eristavi's current fixed grammar. It is not a claim of universally fastest parsing. Measure the implementation before claiming speedups.

## Evidence and current baseline
Reviewed GRAMMAR.md, PRECEDENCE.md, src/compiler/parser.eri, parser_state.eri, ast.eri, compiler/erist/parser.py, syntax.py, and existing frontend report/test machinery. The inspected snapshot is PR 57 head 8af0ffe3350c737550c3ab0e6c3fa89f60f6f091, confirmed still the PR head during this review.

Both implementations already use recursive descent and explicit expression precedence levels. The self-hosted AST uses one generic Node with kind, token index, first/second/third/next, text, extra, and flag. Its meaning depends on node kind. Parameters and declared failures share one linked chain, with a flag distinguishing failures. The self-hosted parser scans for known type names and import aliases, then uses linear Text membership checks when recognizing constructions. Qualified paths are assembled as Text. Nodes retain token indices, coupling location reporting to token retention.

These are concrete representation and boundary opportunities. Their contribution to full compiler time has not been measured. This parser proposal is not presented as the established cure for the owned self-build timeout.

## 1. Parsing strategy
Keep one per-file cursor over the immutable token buffer. Use small current-kind, lookahead-kind, advance, match, and expect operations. Read full token fields only when needed. Avoid copying token records and materializing source text on common dispatch paths.

Dispatch statements and declarations by token kind. Use direct calls for fixed grammar forms. Avoid token cursor rewinding and speculative whole-expression reparsing. The syntax-hint prepass described below is explicit and separate from the main forward parse.

Use loops for statement sequences, child lists, left-associative binary operators, postfix chains, and runs of equal-precedence prefix operators. Use guarded recursion for genuine syntactic nesting. Every loop must consume input, finish, or return an error.

An LR parser, GLR parser, PEG/packrat engine, or generic parser-combinator runtime is not justified by the present grammar and goals. A general Pratt parser is a reasonable alternative, but switching the existing correct precedence architecture has no demonstrated performance benefit. The proposal retains explicit tiers for simpler auditing of the current language restrictions.

## 2. Exact expression grammar
Preserve this high-to-low ordering:

| Level | Forms | Rule |
|---|---|---|
| 1 | Calls, indexing, member access | Postfix, left-to-right |
| 2 | Unary minus, try, identity | Prefix |
| 3 | Multiplication, division, remainder | Left-associative |
| 4 | Addition, subtraction | Left-associative |
| 5 | Equality and ordering comparisons | At most one unparenthesized comparison |
| 6 | not | Prefix, below comparisons |
| 7 | and | Left-associative |
| 8 | or | Left-associative |

For example, not a == b parses as not (a == b). A comparison chain such as a < b < c is rejected. Assignment remains outside expression parsing.

Keep prefix admissibility grammar-exact: a generic binding-power implementation must not accidentally accept an unparenthesized not expression where an additive operand is required. Parenthesized expressions have their own normal expression entry.

Keep operator kinds as compact tags, not allocated Text. Preserve tree order. Do not reassociate arithmetic, short-circuit operators, or checked operations during parsing.

Numeric literals remain source-backed syntax. Do not prematurely reject a positive magnitude that needs surrounding unary-minus context for the minimum signed Int value; frontend literal processing owns conversion and range semantics.

## 3. Construction versus block: preserve the actual language
The sequence Name { ... } needs contextual classification because Eristavi uses braces for both construction and structural blocks. A field initializer can also resemble a statement in a block.

The current implementation uses locally declared type/error names and import aliases as syntactic hints. Removing these hints and deciding that every brace begins a construction, or every control-flow-header brace begins a block, would change behavior.

For this redesign:
- Retain a small per-file SyntaxHints index built by one bounded forward token scan.
- Store relevant names as SymbolIds in exact-membership hash sets, with checked growth and exact key equality.
- Preserve the current classification behavior, including forward declarations and qualified imported roots.
- Do not load imported files, resolve symbols, or run type inference inside the parser.
- Track whether an expression is a qualified-name candidate, and its root SymbolId, without repeatedly assembling path Text or recursively walking the same prefix.
- Once classification commits to a construction, report a construction syntax error directly rather than backtracking into a block interpretation.

The hint scan must be specified against the existing implementation, including malformed-input error priority. Fixing an existing ambiguity or accepting new construction cases requires separate, explicit grammar/compatibility review. The parser algorithm alone cannot remove this constraint.

This is an intentional compatibility boundary. It means the proposed parser is not advertised as completely independent of syntactic name hints.

## 4. Handlers and assignment
Retain separate expression and value-expression entry points. A value-expression parses an ordinary expression followed by zero or more else error handlers in precisely the contexts currently supported. Do not broaden handlers to every expression position as an incidental refactor.

Two-token recognition distinguishes else error from the conditional else form. Parse handler type syntax and body structure; leave exhaustiveness, checked-failure compatibility, and control-flow completion to semantic analysis.

Parse a statement-leading expression once. If the next token is assignment, classify its target syntax and parse the right side as a value-expression. Otherwise parse any permitted handler tail and the expression-statement terminator. Assignment never enters the expression operator table, and chained assignment remains invalid.

Syntactic target shape and semantic writeability are different checks. Name binding, mutability, type compatibility, and supported indexing remain semantic. Any relocation of an existing diagnostic between phases must be reviewed rather than silently accepted.

## 5. Compact AST storage
One module owns its syntax storage. Use append-only, contiguous buffers for separate categories:
- expressions;
- statements;
- declarations;
- type references;
- parameters, field declarations/initializers, and handlers as distinct payload categories where required.

Use category-specific tagged records and kind-specific payloads behind checked constructors/accessors. Large or uncommon payloads may use separate indexed payload arrays. The API must describe actual fields, not a public bag of interchangeable first/second/third fields.

Use distinct ExprId, StmtId, DeclId, TypeRefId, and appropriate auxiliary IDs. Each occupies 32 bits in storage, is scoped to its owning module/table, and reserves zero for absence. Check exhaustion. Numeric IDs are not stable across edits or compilation sessions.

Separate function parameter lists and declared-failure lists. Preserve source order for module contents and block items; declaration references must remain representable wherever existing syntax admits them. Do not change declaration-placement rules through AST encoding.

Use checked internal storage facilities already agreed for the lexer. An ordinary List of individually boxed records does not satisfy the contiguous-storage objective. The exact AST byte layout is chosen from concrete field definitions and measured sizes; the 24-byte token decision does not imply 24-byte AST nodes.

## 6. Variable-length children
Arguments, statements, list elements, parameters, fields, handlers, and qualified-name components use contiguous ID ranges with start/count descriptors in category-appropriate pools. Ranges are checked against pool limits.

Nested lists cannot safely append parent and child edges into one unfinished range. Use a reusable scratch stack with per-list marks. After a list is complete, copy its immediate IDs once into the persistent pool and release that scratch segment. This preserves contiguous ranges without repeatedly inserting or shifting parent data.

Build nodes once their children are known. Do not expose partly initialized nodes. IDs survive backing-buffer relocation because they are indices; no escaped raw element references.

## 7. Names, literals, and source spans
Reuse lexer SymbolIds. Store qualified names as pooled sequences of SymbolIds, rendering dotted Text only for reports or diagnostics.

AST literals retain source slices or stable LiteralIds, never scanner scratch or pointers into movable token storage. Preserve the separate owners agreed for source and decoded literals.

Give syntax nodes full source byte spans. Preserve diagnostic anchors separately where an operator, member name, or opening delimiter is the appropriate location. A grouped-expression node can retain parentheses and span information while semantic analysis treats grouping transparently.

SourceId belongs to the module container. ASTs must support later diagnostics after tokens are released. There is no per-node cached line/column. Source maps compute the existing scalar-column locations when needed.

## 8. Parser state and interface
Conceptual inputs: token buffer, source/literal/symbol contexts, module AST builder, limits, and local syntax hints. These are logical components, not a finalized Eristavi function signature.

Parser state owns a cursor, nesting counters, delimiter/context state, scratch storage, and one error result. No global mutable state.

Success returns the complete immutable module AST and its owning storage. Failure returns a structured syntax or resource error and releases partial per-file build storage. Shared compilation tables may retain unused entries within their valid lifetimes.

Do not access files, build module graphs, run semantic checks, or emit IR from parser routines. Parsing source imports records syntax; the module loader owns resolution.

## 9. Diagnostics and resilience
Normal compilation remains fail-fast. Errors contain a stable code, primary source span, expected token kind or compact expected set where useful, actual kind, and optional related opening span. Message formatting is separate.

Preserve existing required diagnostic text, classification, locations, and selection priority through compatibility fixtures/adapters. Additional span detail can be added without changing the selected error. Diagnostic redesigns require explicit review.

No partial AST is passed as valid to semantic analysis. Recovery nodes, several-error reporting, and IDE parsing would require an explicit future mode and contract.

Guard nesting before host-stack exhaustion. Parse long flat sequences and prefix runs iteratively. Nesting, ID, size, and allocation exhaustion must produce controlled resource errors, not syntax misclassification, hangs, or crashes. Choose configurable limits using the actual backend's frame costs; do not invent a universal safe depth.

Later AST visitors must also handle long left-deep expression trees safely, using explicit stacks where necessary. An iterative parser does not automatically make recursive semantic visitors safe.

## 10. Boundaries with semantics and Universal IR
The AST represents Eristavi syntax. Semantic facts live in separate typed tables keyed by AST IDs, including bindings, inferred types, checked failures, ownership/resource facts, and reachability where needed.

Do not mutate syntax nodes into semantic or IR nodes. Type-annotated syntax variants are not the same as a separate materialized Typed IR.

The intended frontend path is syntax AST plus semantic facts into the agreed typed Universal IR. Release AST storage after its final consumer has finished, keeping required diagnostics and source mapping independent.

Construct the AST directly. A second full concrete-syntax tree or event-log representation is not required on the normal batch compiler path. This choice does not promise a lossless editable IDE tree; original source bytes remain available, while structural comment attachment and incremental reparsing are future tooling work.

## 11. Complexity and performance expectations
For fixed grammar size, bounded token work, append-only construction, and expected constant-time syntax-hint membership:
- expected main parsing and AST construction are O(T), where T is token count;
- the hint scan is an additional O(T) pass;
- storage is O(T), including nodes, edges, and worst-case scratch;
- genuinely nested syntax uses O(D) guarded call-stack depth, with D bounded by configured resource limits.

Hash lookup is not a worst-case constant-time guarantee. Measure collision behavior and enforce resource limits. Source normalization/interning belongs to lexer preparation and must not be silently counted as free in frontend measurements.

Expected benefits are fewer individual allocations, less pointer traversal, less Text copying, and more direct node access. These remain hypotheses until measured. Parser improvements do not imply the same percentage improvement in full compilation or generated program speed.

## 12. Verification and migration
Recommended integration sequence:
1. Specify typed AST constructors/accessors and compatibility reporting.
2. Implement shared packed-storage support and AST buffers.
3. Implement indexed syntax hints and parser cursor operations.
4. Port precedence, postfix, declaration, statement, and handler routines while preserving behavior.
5. Integrate AST consumers and remove accidental token-lifetime dependencies.
6. Run focused validation and paired parser measurements.
7. Run broad compiler qualification once the replacement slice is ready.

Acceptance checks:
- Normalize old and new trees into the existing eristavi-ast-v1 reporting contract, adapting new grouping/full-span metadata without changing old observable anchors.
- Compare valid source across repository files, the existing frontend fixtures, and the reference parser. Where implementations disagree, resolve against locked language rules rather than taking majority behavior as truth.
- Compare malformed-input errors, including multiple-defect files, delimiter errors, forbidden aliases, invalid comparison chains, and invalid assignment placement.
- Cover not precedence, mixed prefixes, long postfix/binary chains, nested argument lists, handler contexts, constructions adjacent to blocks, forward names, qualified imports, Unicode names, empty lists, and signed-Int boundary syntax.
- Exercise low injected resource limits, failed growth, ID exhaustion, deep nesting, and safe failure cleanup.
- Verify token-release independence, storage relocation, child ranges, required fields, and category-correct IDs.
- Use grammar-driven valid-input generation and token mutation for targeted fuzzing. Differential agreement is evidence, not proof of grammar correctness.
- Measure parser-only time using already prepared tokens, and separately measure total source preparation plus lexing plus parsing. Report peak memory, allocations, lookup counts, and size scaling on comparable inputs and build settings.

Use local constructor invariants in production. Full structural AST checks are useful during migration/testing; this proposal does not add a mandatory redundant whole-AST traversal to every compile. Preserve mandatory semantic and Universal IR verification.

No implementation changes, benchmark runs, new CI workflows, or compiler self-builds were performed for this proposal.

## References
Repository baseline: https://github.com/eristavi/eristavi-lang/tree/8af0ffe3350c737550c3ab0e6c3fa89f60f6f091
Grammar: https://github.com/eristavi/eristavi-lang/blob/8af0ffe3350c737550c3ab0e6c3fa89f60f6f091/GRAMMAR.md
Self-hosted parser: https://github.com/eristavi/eristavi-lang/blob/8af0ffe3350c737550c3ab0e6c3fa89f60f6f091/src/compiler/parser.eri
Self-hosted AST: https://github.com/eristavi/eristavi-lang/blob/8af0ffe3350c737550c3ab0e6c3fa89f60f6f091/src/compiler/ast.eri
Rust compiler overview documents recursive descent: https://rustc-dev-guide.rust-lang.org/overview.html
LLVM's frontend tutorial demonstrates combining recursive descent with operator precedence; its tutorial implementation is not a production architecture specification: https://llvm.org/docs/tutorial/MyFirstLanguageFrontend/LangImpl02.html
Rust-analyzer's syntax guide explains its different full-fidelity IDE-tree goals and a recursive-descent/Pratt combination. It describes an older architecture snapshot and is used as context, not a current performance claim: https://rust-analyzer.github.io/book/contributing/syntax.html

