# Eristavi Lexical Rules

> **Status: Partially locked for pre-0.1**

This document records lexical rules required by the first Eristavi lexer. Rules are added here only after they are explicitly decided.

## 1. Comments — locked

Eristavi supports exactly two comment forms.

### Line comments

A line comment begins with `//` and continues to the end of the physical source line.

```eri
// This is a comment.
let price be 50; // This is also a comment.
```

The terminating newline is not part of the comment token. Newlines remain ordinary whitespace and do not terminate Eristavi statements.

### Block comments

A block comment begins with `/*` and ends with the matching `*/`.

```eri
/*
    This is a block comment.
    It may span multiple lines.
*/
```

Block comments may appear where whitespace is permitted.

### Nested block comments

Block comments are nestable.

```eri
/*
    Outer comment.

    /*
        Nested comment.
    */

    Back in the outer comment.
*/
```

The lexer must track nesting depth. Each nested `/*` increases the depth by one; each matching `*/` decreases it by one. The comment ends when the depth returns to zero.

An unterminated block comment is a lexical error and should report the source location where the block comment began.

### No alternate comment markers

Pre-0.1 does not define alternate comment forms such as:

```text
# comment
-- comment
/// comment
```

This preserves one obvious line-comment form and one obvious block-comment form.

### Governing rule

> Use `//` for line comments and nestable `/* ... */` for block comments.

## 2. Identifiers — locked

Eristavi identifiers are Unicode-aware and follow the Unicode identifier model rather than being limited to ASCII letters.

Conceptually:

```text
identifier-start    := "_" | XID_Start
identifier-continue := "_" | XID_Continue
identifier          := identifier-start { identifier-continue }
```

`XID_Start` and `XID_Continue` refer to the corresponding Unicode identifier properties used for stable programming-language identifiers.

Examples of valid identifiers include:

```eri
let customerName be "Anna";
let customer2 be "Maria";
let _temporary be 10;
let customer_id be 10;

let имя be "Anna";
let τιμή be 50;
let café be "Open";
```

### Digits

Digits may appear after the first identifier character but cannot begin an identifier.

Valid:

```eri
let room101 be 101;
```

Invalid:

```text
101room
```

This keeps identifiers lexically distinct from numeric literals.

### Underscore

`_` is permitted at the beginning of an identifier and within an identifier.

```eri
let _cache be [];
let customer_id be 10;
```

Underscore has no hidden language meaning in pre-0.1. Names beginning with `_`, including `_` itself when otherwise valid in context, are ordinary identifiers rather than implicit privacy, discard, compiler, or special-runtime markers.

### No hyphens or arbitrary symbols

A hyphen is not part of an identifier because `-` is an operator.

```text
customer-name   // not one identifier
```

Emoji and arbitrary symbols are not identifier characters merely because they are valid Unicode text.

Examples such as these are not valid identifiers:

```text
🚀customer
💰price
❤️
```

Unicode support is therefore broad but constrained by the XID identifier properties.

### Case sensitivity

Identifiers are case-sensitive.

```text
customer
Customer
CUSTOMER
```

are three distinct identifiers.

This allows ordinary code such as:

```eri
let customer be Customer {
    name = "Anna";
};
```

without special casing between value names and type names.

### NFC normalization

Identifier spelling is normalized to Unicode NFC for identity and comparison.

Two source spellings that differ only in canonically equivalent Unicode encoding therefore refer to the same identifier after normalization.

This normalization applies to identifier identity, not to ordinary `Text` values. Eristavi's existing rule that `Text` is not silently normalized remains unchanged.

### Reserved keywords

A reserved Eristavi keyword cannot be used as an identifier.

For example:

```text
function
let
if
return
```

cannot be ordinary variable, function, field, type, error, or module-segment names where the lexer recognizes them as keywords.

Pre-0.1 does not define escaped identifiers such as:

```text
`function`
@function
```

If a word is reserved, the programmer chooses another name.

The exact pre-0.1 keyword set is defined separately in the keyword section of this lexical specification.

### Same rule across named declarations

The same identifier rule applies consistently to:

- local bindings;
- functions;
- parameters;
- type names;
- field names;
- error names;
- module path segments;
- import aliases;
- other ordinary programmer-defined names.

Eristavi does not create separate lexical alphabets for different categories of declarations.

### Naming style is not grammar

The language grammar does not enforce casing conventions such as camelCase or PascalCase.

The recommended project style may use forms such as:

```eri
let customerName be "Anna";

function calculateTotal() {
    ...
}

type CustomerAccount {
    ...
}

error DatabaseError {
    message Text;
}
```

Such conventions belong to formatting, linting, and project style rather than lexical validity.

### No semantic magic from spelling

An identifier does not acquire privacy, mutability, storage, compiler ownership, or another semantic property from its spelling or capitalization.

Language semantics come from explicit Eristavi constructs.

### Governing rule

> Eristavi identifiers use Unicode XID rules, normalize to NFC for identifier identity, remain case-sensitive, allow `_`, reserve keywords, and assign no hidden semantics to naming style.
