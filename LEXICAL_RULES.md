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

### Standard `output` is not a keyword

`output` is not part of the pre-0.1 reserved keyword set.

The lexer treats `output` as an ordinary identifier. Name resolution supplies the predeclared standard textual-output function described in `OUTPUT.md`.

This means the keyword set remains exactly 28 words; standard-library conveniences do not become grammar merely because they are available without an explicit import.

Names such as `print`, `echo`, `say`, and `out` are also not reserved and have no built-in output meaning in pre-0.1.

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

## 5. Integer literals — locked

Pre-0.1 supports decimal, binary, and hexadecimal integer literals.

Examples:

```eri
let decimal be 1_000_000;
let flags be 0b1010_0011;
let mask be 0xFF_00;
```

### Decimal literals

A decimal integer literal is either `0` or a nonzero decimal digit followed by zero or more decimal digits, with optional underscore separators between digits.

Examples:

```eri
0
1
42
1_000_000
9_223_372_036_854_775_807
```

Leading zeroes are rejected except for the literal `0` itself.

```text
0      valid
7      valid
007    invalid
```

Eristavi therefore never interprets a leading zero as octal notation.

### Binary literals

A binary integer literal begins with the lowercase prefix `0b` followed by one or more binary digits.

```eri
0b0
0b1010
0b1010_0110
```

Only `0` and `1` are valid binary digits.

### Hexadecimal literals

A hexadecimal integer literal begins with the lowercase prefix `0x` followed by one or more hexadecimal digits.

```eri
0x0
0xFF
0xff
0xDeAdBeEf
0xFF_A0
```

The prefix is lowercase, while hexadecimal digits `A` through `F` may be written in either case.

### Underscore separators

Underscores are allowed only between digits of the same literal.

Valid:

```eri
1_000
0b1010_0110
0xFF_A0
```

Invalid:

```text
_100
100_
1__000
0x_FF
0b_1010
```

Underscores affect readability only and do not change the numeric value.

### Negative integers use unary minus

The minus sign is not part of an integer-literal token.

```eri
-50
```

is parsed conceptually as unary `-` applied to the positive integer literal `50`.

The same unary operator therefore works consistently with names and grouped expressions:

```eri
let a be -count;
let b be -(x + y);
```

### `Int` range checking

`Int` remains the locked signed 64-bit integer type.

The ordinary positive `Int` maximum is:

```text
9223372036854775807
```

The minimum is:

```text
-9223372036854775808
```

Because the minus sign is a unary operator rather than part of the literal token, constant evaluation must allow the magnitude `9223372036854775808` when it is immediately negated to form the valid minimum `Int` value.

A literal or constant expression that cannot be represented by its required integer type is rejected at compile time.

### No octal literals in pre-0.1

Pre-0.1 does not define an octal literal prefix such as:

```text
0o755
```

Octal notation may be considered later only if real systems-programming use cases justify it.

### No integer suffixes

Pre-0.1 does not define literal suffixes such as:

```text
42i64
42u32
42L
```

The ordinary integer type is already `Int`. Future narrower, wider, or unsigned integer types should not force suffix syntax into the initial language unless a demonstrated need emerges.

### Conceptual lexical forms

```text
decimal-integer :=
    "0"
    | nonzero-decimal-digit { [ "_" ] decimal-digit }

binary-integer :=
    "0b" binary-digit { [ "_" ] binary-digit }

hex-integer :=
    "0x" hex-digit { [ "_" ] hex-digit }
```

The implementation must additionally enforce that `_` occurs only between digits, never consecutively or at either edge of the digit sequence.

### Governing rule

> Pre-0.1 integer literals use decimal, `0b` binary, or `0x` hexadecimal notation. `_` is a readability separator only between digits, leading-zero decimal forms and octal notation are rejected, and negative values are expressed through the ordinary unary minus operator rather than a signed literal token.

## 6. Floating-point literals — locked

Pre-0.1 floating-point literals use decimal notation only.

Examples:

```eri
0.0
1.5
19.95
1_000.50
3.141_592_653
1e6
1E6
1.5e3
1.5e-3
1.5E+3
```

### Float recognition

A numeric literal is recognized as a floating-point literal when it contains either:

- a decimal point with at least one digit on both sides; or
- a decimal exponent introduced by `e` or `E`.

Therefore:

```eri
10      // Int literal
10.0    // Float literal
10e2    // Float literal
10E2    // Float literal
```

### Digits are required on both sides of the decimal point

Shorthand decimal forms are not valid:

```text
.5
5.
```

Use:

```eri
0.5
5.0
```

This keeps decimal literals explicit and prevents unnecessary ambiguity with the `.` token used for member and module access.

### Scientific notation

A decimal exponent begins with `e` or `E`, optionally followed by `+` or `-`, and then a digit sequence.

Valid examples:

```eri
1e6
1E6
2.5e8
4.2e-10
4.2E+10
```

Both `e` and `E` are accepted source spellings because they express the same universally understood scientific-notation concept without changing the programmer's mental model.

The canonical formatter representation uses lowercase `e`.

For example, source written as:

```eri
2.5E-8
```

may be formatted canonically as:

```eri
2.5e-8
```

### Underscore separators

As with integer literals, underscores are readability separators and are valid only between digits.

Valid:

```eri
1_000.25
1.000_001
6.022_140_76e23
1e1_000
```

Invalid:

```text
_1.0
1_.0
1._0
1.0_
1e_10
1e10_
1__000.0
```

Underscores do not change the numeric value.

### Negative floats use unary minus

The minus sign is not part of the floating-point literal token.

```eri
-19.95
```

is parsed as unary `-` applied to the positive floating-point literal `19.95`.

This preserves one consistent unary-negation rule for numeric literals, names, and grouped expressions.

### Decimal notation only

Pre-0.1 does not define hexadecimal or binary floating-point literal forms such as:

```text
0x1.2p3
0b1.01
```

Binary and hexadecimal notation remain useful for integer masks and low-level integer work, but do not create additional floating-point literal families.

### No floating-point suffixes

Pre-0.1 does not define suffixes such as:

```text
1.0f
1.0f32
1.0f64
1.0d
```

`Float` has one language-defined semantic meaning. If future numeric types are added, their conversion and literal interaction should be designed explicitly rather than forcing suffix syntax into the initial language.

### No special NaN or infinity literal tokens

Pre-0.1 does not reserve lexical forms such as:

```text
NaN
Infinity
-inf
```

If the eventual `Float` semantic model exposes non-finite values, they should be provided through the type or standard library rather than by expanding the lexer vocabulary unnecessarily.

### Conceptual lexical forms

```text
digit-sequence :=
    decimal-digit { [ "_" ] decimal-digit }

exponent :=
    ( "e" | "E" ) [ "+" | "-" ] digit-sequence

fractional-float :=
    digit-sequence "." digit-sequence [ exponent ]

exponent-float :=
    digit-sequence exponent

float-literal :=
    fractional-float
    | exponent-float
```

The implementation must enforce that `_` occurs only between digits and never at an edge, adjacent to `.`, adjacent to `e`/`E`, or adjacent to the exponent sign.

### Semantic representation remains separate

This section locks only floating-point literal syntax.

The exact semantic definition of `Float`—including representation, precision, rounding, overflow, non-finite values, and arithmetic behavior—is a separate language-semantic decision and is not implied by the literal spelling rules.

### Governing rule

> Pre-0.1 floating-point literals are decimal, require either a decimal point with digits on both sides or an `e`/`E` exponent, allow `_` only between digits, use the ordinary unary minus operator for negative values, and define no suffixes or alternate-base float forms. Lowercase `e` is the canonical formatter spelling.

## 7. Whitespace — locked

Whitespace is syntactically insignificant except where separation is required to prevent adjacent source characters from forming a different token.

These forms are therefore equivalent:

```eri
let price be 50;
```

```eri
let    price    be    50;
```

```eri
let price
    be
    50;
```

### No indentation-based syntax

Indentation has no grammatical meaning.

This is syntactically valid:

```eri
if ready {
output("Ready");
}
```

A formatter may produce a conventional layout, but indentation depth never changes program structure.

### Newlines never terminate statements

Eristavi does not use automatic semicolon insertion or any equivalent newline-based statement termination.

Simple statements are terminated explicitly by `;`; structural blocks are delimited by `{` and `}`.

For example:

```eri
let total be
    price
    + tax
    + delivery;
```

is one statement regardless of its physical line breaks.

A newline is ordinary whitespace outside contexts where another lexical rule explicitly says otherwise, such as the prohibition on physical newlines inside ordinary `Text` literals.

### Recognized whitespace characters

Pre-0.1 recognizes exactly these source whitespace characters:

```text
U+0020  SPACE
U+0009  CHARACTER TABULATION (horizontal tab)
U+000A  LINE FEED
U+000D  CARRIAGE RETURN
```

No other Unicode character is silently treated as source whitespace.

In particular, characters such as these are not ordinary Eristavi whitespace:

```text
U+00A0  NO-BREAK SPACE
U+2003  EM SPACE
U+200B  ZERO WIDTH SPACE
```

When such invisible or unusual characters occur where whitespace appears to have been intended, the compiler should issue a clear diagnostic identifying the character and recommending an ordinary space or supported line break.

### Line ending equivalence

The following line-ending forms have the same language meaning:

```text
LF      \n
CRLF    \r\n
CR      \r
```

A compiler may normalize them internally for source-location tracking, but that normalization must not change program meaning.

### Tabs

A horizontal tab is ordinary whitespace. Its visual width is not part of Eristavi semantics.

Editors and formatters may choose a project style, but parsing must not depend on whether a tab is rendered as two, four, eight, or another number of columns.

### Comments act as token separators

Outside literals, comments behave like whitespace for token separation.

For example:

```eri
let price /* explanation */ be 50;
```

has the same token structure as:

```eri
let price be 50;
```

Removing a comment conceptually must not merge adjacent lexical material into a different token; the lexer treats the comment boundary as a separator where token separation is required.

### Whitespace is required only to separate tokens when necessary

Adjacent word-like characters may form one token rather than two.

For example:

```text
letprice
```

is one identifier, not the two tokens `let` and `price`.

Punctuation normally provides its own token boundary, so surrounding whitespace is not required:

```eri
add(a,b);
a+b;
user.name;
```

Formatting style belongs to the formatter and linter rather than the parser.

### UTF-8 BOM

A leading `U+FEFF` byte-order mark is permitted only as the very first code point of a source file and is ignored there.

`U+FEFF` appearing anywhere else in source is not whitespace and is a lexical error.

### Governing rule

> Eristavi source is formatting-insensitive: space, tab, LF, and CR separate tokens without carrying structure; indentation and newlines have no grammatical meaning; statements are never terminated implicitly by line breaks; comments act as separators; and unusual invisible Unicode whitespace is rejected rather than silently accepted.
