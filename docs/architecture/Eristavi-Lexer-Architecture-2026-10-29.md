# Eristavi lexer architecture — decision record
Date: 2026-10-29
Status: Architecture decisions and acceptance criteria below are agreed in conversation. This record does not represent an implemented lexer or completed validation.

## Scope
Redesign lexer internals while preserving Eristavi's source language, current lexical rules, and observable diagnostic behavior. The existing compiler remains the behavioral reference. Parser, semantic analysis, Universal IR, runtime, and machine lowering require their own architectural decisions.

The design prioritizes predictable storage, explicit ownership, and avoiding unnecessary copying. Performance superiority remains a measurement question.

## 1. Source boundary
The source manager owns one immutable byte snapshot per file and an associated source map. Source loading validates UTF-8 once; invalid UTF-8 retains its existing file-loading error classification. The lexer consumes validated bytes, with bounds checks and scalar decoding where needed.

Source preparation builds the line-start byte-offset table. Preserve existing initial BOM acceptance, diagnostic-column handling, newline behavior, and rejection of BOM elsewhere, including within comments and strings. Preserve existing error-selection precedence when several defects coexist. This is a behavioral contract, not a requirement to fuse all preparation into one pass.

All token offsets refer to the original source snapshot, including any initial BOM bytes. Source contents must remain available while borrowed literal contents or diagnostics require them.

## 2. Token buffer and physical representation
Lex an entire file into an indexed, contiguous token buffer. Streaming production is not the initial interface.

Each token occupies an actual 24-byte record:

| Byte offset | Field | Storage |
|---|---|---|
| 0 | start_byte | unsigned 64-bit |
| 8 | end_byte | unsigned 64-bit |
| 16 | payload_id | unsigned 32-bit |
| 20 | kind | unsigned 16-bit |
| 22 | reserved | unsigned 16-bit, initially zero |

Spans are half-open: [start_byte, end_byte). SourceId belongs to the containing token buffer rather than every token.

A list of separately boxed ordinary language records does not satisfy the physical-storage decision. Implementation must establish the actual layout and stride through an appropriate storage facility. Neither a binary serialization format nor a stable external token ABI is defined here.

Check capacity growth, byte-size multiplication, cursor conversion, and ID exhaustion before overflow. Resource limits are distinct from malformed-source errors.

## 3. Scanner
Use a forward byte cursor, an ASCII fast path, bounded lookahead, and UTF-8 scalar decoding for non-ASCII input. Do not allocate a Text object for each character. End-of-input follows byte bounds; an actual zero byte is source input and must follow existing lexical rules.

The scanning algorithm targets linear work in source length. Unicode normalization, identifier-table operations, literal decoding, and diagnostic formatting have separately measurable costs. Do not describe the entire frontend as worst-case linear merely because cursor traversal is linear.

## 4. Identifiers
Use one identifier table scoped to a compilation and shared across its files.

Preserve the language's pinned Unicode XID rules, NFC identity, and case sensitivity. Original spelling remains accessible through the source span. Intern normalized identifier names and reference them with a 32-bit SymbolId.

Hashing selects candidates; exact normalized-name comparison determines identity. A SymbolId denotes a spelling, not a declaration or resolved binding. IDs are internal to the owning compilation and are not permanent module or cache identities.

## 5. Keywords, operators, and comments
Maintain one authoritative definition of token kinds and fixed spellings. Scan the complete identifier, apply the agreed normalization, and classify the complete name against the existing keyword set. A keyword prefix must never split a longer identifier.

Use static keyword dispatch by length and exact spelling initially. Alternative lookup strategies require evidence before adding complexity.

Choose the longest valid operator match. Recognize comment-opening delimiters before conflicting operator tokens, preserving current lexical precedence and nested-comment behavior.

Whitespace and comments do not become parser tokens. Their source text remains in the source snapshot.

## 6. Literals and payloads
The lexer validates numeric spelling, base, separators, and floating-point syntax. Later frontend literal processing performs numeric conversion and range checking in the appropriate semantic context. This does not introduce a separate Typed IR.

Unescaped Text contents borrow from the source. Escaped Text is validated and decoded once into separate growable literal storage. The token span preserves complete original spelling in either case. Mandatory Text interning or deduplication is not part of lexing.

| Token category | payload_id |
|---|---|
| Identifier | Nonzero SymbolId into the identifier table |
| Text without escapes | Zero; contents borrowed from source |
| Text requiring decoding | Nonzero LiteralId into decoded literal storage |
| Number | Zero; spelling obtained from source span |
| Keyword, operator, punctuation, EOF | Zero |

Zero is reserved. Valid stored IDs occupy 1 through UINT32_MAX, subject to practical resource limits and checked exhaustion. Token kind determines the table and interpretation. Compiler APIs expose distinct SymbolId and LiteralId types even though the token stores both in the same 32-bit field.

References into growable storage use stable IDs or offsets. Raw references must not become invalid when storage grows.

## 7. Source locations and errors
Each file has a source map with indexed line-start byte offsets. Tokens store byte spans; diagnostics compute existing one-based lines and Unicode-scalar columns as needed. Preserve initial BOM, CR/LF, CRLF, and tab behavior. Add checkpoints for repeated expensive location queries only if measurements justify them.

Lexical errors contain a structured code, SourceId, offending span, and an optional related span, such as an opening delimiter. A separate formatter produces diagnostic text and locations.

Normal compilation is fail-fast under existing error-selection precedence. The parser receives either a complete token buffer or an error. There are no partial parser-visible token buffers or implicit recovery tokens. Recovery for editors would require an explicit future mode.

## 8. Ownership and release
Use separate owners and explicit phase-based cleanup after all consumers of the storage have finished.

| Storage | Owner | Release boundary |
|---|---|---|
| Immutable bytes and source map | Compilation source manager | After diagnostic and borrowed-content consumers finish |
| Token records | Per-file token buffer | After parsing and other token consumers finish |
| Normalized identifier names | Compilation identifier table | End of compilation |
| Decoded Text values | Separate literal storage | After final consumer finishes or values are transferred |
| Scanner scratch | Individual lexer invocation | Lexing returns or fails |

Token records do not own data required by later stages. Parser and later representations may retain literal IDs or source spans after token records are released, provided the corresponding owners remain alive.

No process-global mutable lexer state. Pass contexts explicitly. No retained references into scanner scratch. Clean up on success and failure. Bulk allocation and release are preferred where practical; the design does not require individual reference counting for every token or literal.

On a lexical failure, shared tables may contain unused entries if their ownership remains valid; this record does not require transactional rollback of compilation-wide interning.

This ownership separation permits independent file scanning later. Parallel scanning and synchronization of shared interning are separate future implementation decisions.

## 9. Parser interface
Successful lexing returns a complete immutable token buffer ending in exactly one EOF token. EOF has span [source_length, source_length). Empty source produces only EOF.

The parser owns its own cursor. Lookahead beyond the last token returns the existing EOF token without allocating or appending tokens. The parser accesses tokens and shared source data through explicit interfaces and does not depend on scanner state.

## 10. Agreed acceptance criteria
These are release gates for the lexer replacement, not claims of completed work.

### Language compatibility
- Compare old and new lexers on repository source files and the existing lexical conformance corpus.
- Preserve token kinds, spelling classification, and decoded literal values for accepted source.
- Compare spans and diagnostic positions after mapping the old representation to the new source-map representation.
- Preserve error classification, offending locations, and selection precedence for rejected source, including files with several defects.
- Exercise complete-name keyword classification, shared operator prefixes, comment delimiters and nesting, number syntax, escape syntax, Unicode identifiers, NFC-equivalent names, BOM placement, actual zero bytes, and EOF.

### Representation and boundaries
- Establish actual token size, field offsets, and contiguous 24-byte stride.
- Verify source bounds and valid span boundaries for every emitted token.
- Verify payload kinds, reserved zero, scoped ID use, and exact-name comparison under hash collisions.
- Verify exactly one EOF, empty input, and repeated lookahead beyond EOF.
- Exercise checked growth, size arithmetic, ID exhaustion, and allocation failure through controlled limits rather than allocating billions of entries.

### Lifetime and failure behavior
- Retain AST literal references after releasing the token buffer and confirm they remain valid.
- Resolve diagnostics after token release while the source manager remains alive.
- Force storage growth and confirm retained IDs or offsets still resolve.
- Verify failure cleanup and that no scanner-scratch references escape.
- Confirm separate compilation contexts do not accidentally share mutable lexer state.

### Performance evidence
- Compare elapsed time, throughput, peak memory, and allocation counts against the existing lexer using identical input and comparable build settings.
- Include typical compiler files, large files, many short tokens, long identifiers, Unicode-heavy source, and escaped Text.
- Measure scaling as input grows, separating source preparation, scanning, normalization/interning, and literal decoding where practical.
- Investigate regressions and unexpected superlinear growth. Agree numerical performance gates from baseline measurements rather than inventing thresholds now.
- Use focused lexer validation during implementation; schedule broad compiler qualification after the replacement slice is integrated.

## 11. Implementation details still to resolve
The packed-buffer and restricted internal-interface decisions in section 12 are agreed. Concrete allocation mechanisms, literal-store backing, identifier hash strategy, token numeric assignments, public API signatures, and migration patch sequence remain to be resolved within those contracts.

The acceptance criteria in section 10 are agreed. No source-language changes, production lexer replacement, benchmark results, or test passes are asserted by this document.

## 12. Packed buffer and restricted internal storage interface
Use a compiler-internal packed token buffer with one contiguous backing allocation at a time, checked geometric growth, indexed fixed-width field access, and one owner responsible for release. Growth may temporarily require both the old and replacement allocations. The buffer is mutable during lexing and read-only after successful completion. Initial capacity and growth factor are measured implementation choices.

Keep platform-specific memory code outside the lexer and parser. The token buffer enforces layout, bounds, growth, and ownership. A restricted internal memory interface provides allocation, copying, fixed-width loads and stores, and release. Target implementations supply machine and platform operations.

The buffer owns an opaque storage handle; raw addresses remain confined beneath the abstraction. Access to these facilities requires an explicit compiler/runtime build capability, not special treatment based on a module filename. Ordinary Eristavi source rules remain unchanged. Other compiler structures may use the same foundation while defining their own layouts.

## 13. Agreed file-extension policy
All Eristavi implementation source, including the lexer, parser, IR implementation, and compiler, retains the primary .eri extension. Internal module roles do not create different source languages or source-file extensions.

Distinct extensions may be introduced for genuinely different generated or serialized formats when those formats are designed. The illustrative .erlx extension is not selected or reserved by this decision. A saved IR format must identify its format and version in its contents rather than relying solely on the filename.

Follow target-platform conventions for native objects (.o or .obj) and compiler executables (erist or erist.exe). Preserve .erist as reserved for a possible distinct future purpose rather than an equivalent source extension.

During ordinary compilation, tokens and IR pass between stages in memory. Introducing an output extension does not require intermediate files on the normal compilation path.

