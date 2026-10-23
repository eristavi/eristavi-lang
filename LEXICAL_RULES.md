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

Pre-0.1 does not define escaped identifiers such as:

```text
`function`
@function
```

If a word is reserved, the programmer chooses another name.

The exact pre-0.1 keyword set is defined in the next section.

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

## 3. Reserved keywords — locked

Pre-0.1 reserves exactly the words required by the currently defined grammar.

The reserved keyword set is:

```text
let
fixed
be
function
returns
return
if
else
for
in
while
type
identity
maybe
error
fails
fail
try
with
import
as
public
and
or
not
true
false
none
```

There are 28 reserved keywords in pre-0.1.

### Keyword groups

For readability, the set may be understood by role:

```text
Bindings:
let fixed be

Functions:
function returns return

Control flow:
if else for in while

Types and value semantics:
type identity maybe

Checked errors:
error fails fail try

Resources:
with

Modules and visibility:
import as public

Boolean operators:
and or not

Literal words:
true false none
```

### Exact lowercase spelling

Keyword recognition is case-sensitive and uses the exact lowercase spelling.

For example:

```eri
let value be 10;
```

uses the keyword `let`, while `Let` is lexically an identifier:

```eri
let Let be 10;
```

Whether a particular identifier is then valid in semantic context is checked normally by later compiler stages.

### Keywords cannot be identifiers

Reserved keywords cannot be used as ordinary programmer-defined names.

These are invalid:

```text
let function be 10;
let return be 20;
let type be "Customer";
```

Pre-0.1 has no escaped-keyword mechanism such as backticks or `@` prefixes.

### Built-in types are not lexical keywords

Names such as:

```text
Int
Float
Bool
Text
```

are predeclared type names, not reserved lexical keywords.

A lexer may therefore tokenize `Int` as an identifier-like name, while semantic analysis resolves it to the built-in `Int` type.

This keeps grammar vocabulary separate from the set of predeclared library or type-system names.

### Reserved module namespace is not a keyword

`std` is reserved for the Eristavi standard-library module namespace, but it is not a lexical keyword.

Its special status is enforced by module/name resolution rather than by the lexer.

### `print` is not reserved

`print` is not part of the pre-0.1 reserved keyword set.

The bootstrap compiler may temporarily provide it as an intrinsic or library-visible operation, but its final classification remains separate from lexical keyword design.

### Future vocabulary is not pre-reserved

Words are not reserved merely because they might become useful in a future version.

For example, pre-0.1 does not reserve:

```text
async
await
match
trait
interface
class
enum
break
continue
switch
case
throw
catch
new
static
const
ref
mut
self
```

A future language version may only reserve a new word through an explicit language-design decision.

### Governing rule

> Reserve only vocabulary that already has defined grammatical meaning. Do not consume future words speculatively.

## 4. Text literals and escape sequences — locked

A pre-0.1 `Text` literal uses double quotes.

```eri
let name be "Anna";
let city be "Paphos";
let greeting be "Hello 👋";
```

Eristavi source is UTF-8, so Unicode characters may normally be written directly in source.

### One ordinary string delimiter

Only double quotes delimit ordinary pre-0.1 `Text` literals:

```eri
"Hello"
```

Single-quoted literals are not part of pre-0.1. Eristavi does not define a separate `Char` literal syntax at this stage.

### Escape sequences

Pre-0.1 supports exactly these simple escape sequences inside `Text` literals:

```text
\"     double quote
\\     backslash
\n     newline
\r     carriage return
\t     horizontal tab
\0     NUL character
```

Examples:

```eri
let quote be "She said \"Hello\".";
let path be "C:\\Users\\Revaz";
let message be "First line\nSecond line";
```

An unknown escape is a lexical error. For example:

```text
"\q"
```

is invalid rather than silently becoming `q` or preserving the backslash.

### Unicode scalar escape

A Unicode scalar value may be written with the single escape form:

```text
\u{HEX}
```

Examples:

```eri
let euro be "\u{20AC}";
let smile be "\u{1F600}";
```

Hexadecimal digits inside the braces are case-insensitive. The value must denote a valid Unicode scalar value.

The lexer must reject:

- values greater than `U+10FFFF`;
- surrogate code points `U+D800` through `U+DFFF`;
- an empty `\u{}` escape;
- non-hexadecimal characters inside the escape.

Eristavi does not define separate fixed-width forms such as `\uFFFF` or `\U0001F600` in pre-0.1.

### No byte escape syntax

Pre-0.1 does not define byte-oriented escapes such as:

```text
\x41
```

`Text` represents Unicode text, not arbitrary bytes. Byte-oriented literals belong to a future byte/buffer abstraction if one is needed.

### Physical newlines are not allowed inside ordinary literals

An ordinary `Text` literal cannot cross a physical source line.

This is invalid:

```text
"Hello
world"
```

A newline character is written explicitly:

```eri
let message be "Hello\nworld";
```

An unterminated `Text` literal is a lexical error and should report the location of the opening quote.

### No interpolation in pre-0.1

Pre-0.1 does not define built-in string interpolation forms such as:

```text
"Hello ${name}"
$"Hello {name}"
```

Programs may combine text through ordinary expressions and future formatting-library APIs.

Interpolation may be designed later if real Eristavi programs demonstrate a need for dedicated syntax.

### No raw or multiline string form yet

Pre-0.1 does not define triple-quoted strings, raw strings, heredocs, or another second string-literal family.

This keeps the initial lexer small and leaves room to design a single coherent raw/multiline facility later if required by real use cases such as SQL, HTML, JSON, regular expressions, or embedded source text.

### Unicode preservation

After escape decoding, the resulting `Text` value preserves its Unicode content. String literals are not silently NFC-normalized or otherwise canonically normalized.

This intentionally differs from identifier comparison, where NFC normalization is part of identifier identity.

### Governing rule

> Pre-0.1 `Text` literals are double-quoted UTF-8 text with a small explicit escape set and `\u{...}` scalar escapes. Unknown escapes, physical newlines, invalid Unicode scalars, and unterminated literals are lexical errors; interpolation, raw strings, multiline strings, and byte escapes are postponed.
