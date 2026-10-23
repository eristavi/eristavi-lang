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
