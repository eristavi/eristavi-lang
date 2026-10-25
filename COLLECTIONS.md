# Eristavi Collections

> **Status: Pre-0.1 collection contract; implementation qualification pending**

This document defines Eristavi's fundamental collection/value families.

The governing rule is:

> Write the value naturally. The compiler infers collection relationships where it can, explicit type context is used only where syntax cannot distinguish the value, and Eristavi does not add constructor APIs or exposed generic syntax merely to explain a literal the compiler can already understand.

Pre-0.1 has three fundamental collection-oriented value families:

- `List`: ordered growable homogeneous sequence;
- Map: associative key/value collection inferred from `key : value;` entries;
- `Bytes`: compact binary sequence selected by `Bytes` type context.

`Set`, queue/deque, priority queue, ordered-map variants and other specialized collections remain standard-library/future work.

## 1. One square-bracket collection family of syntax

Square brackets are the visual syntax family for collections.

A List uses comma-separated elements:

```eri
let names be ["Anna", "Maria", "John"];
```

A Map uses colon-separated key/value entries terminated by semicolons:

```eri
let ages be [
    "Anna" : 32;
    "John" : 41;
];
```

Bytes reuses ordinary bracket element syntax only when static context requires `Bytes`:

```eri
let data Bytes be [72, 101, 108, 108, 111];
```

No constructor family is introduced:

```text
list(...)
List(...)
map(...)
Map(...)
bytes(...)
Bytes(...)
```

These are not the canonical collection-construction model.

Braces remain reserved for blocks and typed value construction.

## 2. List

A List is:

- ordered;
- growable;
- homogeneous in its static element relationship;
- an ordinary Eristavi value rather than shared identity by default.

The compiler infers the element relationship:

```eri
let numbers be [1, 2, 3];
let names be ["Anna", "Maria"];
```

Mixed incompatible element relationships are rejected:

```eri
let mixed be [1, "one"]; // compile-time error
```

There is no implicit `Any`, dynamic widening or hidden union.

The pre-0.1 source language does not expose generic spelling such as:

```text
List<Text>
List<Int>
```

Diagnostics may describe an inferred relationship as "List of Text" without making that diagnostic wording source syntax.

### Empty List

`[]` is the empty List literal.

Its element relationship must become known from static context or later statically analyzable use:

```eri
let customers be [];
customers.add(Customer { name = "Anna"; });
```

If no complete element relationship can be inferred, compilation fails.

### Indexing and mutation

List indexing is zero-based and checked:

```eri
let names be ["Anna", "Maria"];
output(names[0]);
names[1] = "Mary";
```

The index must have static type `Int` and satisfy:

```text
0 <= index < count
```

Provably invalid indexes are compile-time errors; otherwise an invalid index produces a defined runtime bounds fault.

A mutable List supports:

```eri
items.add(value);
items[index] = value;
```

`.add(value)` is the single canonical append operation and returns no value.

### Count

Every List exposes read-only `.count` of type `Int`.

### Value semantics

Lists are ordinary values:

```eri
let first be [1, 2];
let second be first;
second.add(3);

output(first.count);  // 2
output(second.count); // 3
```

Mutation of one ordinary List value does not mutate another copied value.

### Equality and iteration

List equality is order-sensitive and element-wise. A List is equality-comparable only when its element relationship is equality-comparable.

`for` traverses List elements from index zero upward using the stable logical sequence present when iteration begins.

## 3. Map

A Map is an associative ordinary value with one statically coherent key relationship and one statically coherent value relationship.

Map syntax is distinguished from List syntax by `:`:

```eri
let ages be [
    "Anna" : 32;
    "John" : 41;
];
```

The compiler infers this as a Map from `Text` to `Int` internally. Pre-0.1 does not require or expose generic source spelling such as `Map<Text, Int>`.

### Empty Map

The unambiguous empty Map literal is:

```eri
let values be [:];
```

As with an empty List, its key and value relationships must become known from static constraints:

```eri
let values be [:];
values["answer"] = 42;
```

If either relationship remains unresolved, compilation fails.

### Homogeneous relationships

All Map keys must share one static type relationship and all values must share one static type relationship.

```eri
let ages be [
    "Anna" : 32;
    "John" : 41;
];
```

This is invalid:

```eri
let mixed be [
    "answer" : 42;
    "name" : "Anna";
];
```

Eristavi does not silently widen the Map value relationship.

### Key types

The initial pre-0.1 Map contract accepts stable scalar keys:

- `Int`;
- `Bool`;
- `Text`.

`Float` is deliberately excluded initially because IEEE NaN equality makes a simple, unsurprising key contract harder to preserve.

Lists, Maps and arbitrary mutable structured values are not Map keys in the initial contract. The key family may be widened later only if equality and hashing remain deterministic and obvious.

### Duplicate literal keys

A duplicate key that is statically obvious in a Map literal is a compile-time error:

```eri
let ages be [
    "Anna" : 32;
    "Anna" : 40;
];
```

Map construction never silently chooses one duplicate literal entry over another.

### Lookup and indexed assignment

Map lookup uses ordinary index syntax:

```eri
output(ages["John"]);
```

The key expression must match the Map key relationship.

Reading a missing key produces the defined runtime fault:

```text
Map key not found
```

It does not silently return `none`, insert a default value, or fabricate a value.

Indexed assignment is the canonical update/insert operation:

```eri
ages["John"] = 42; // update
ages["Maria"] = 28; // insert
```

The key and value must satisfy the inferred Map relationships.

A future safe-lookup library operation may return `maybe T` if real programs demonstrate the need; it is not alternate indexing syntax.

### Count

Every Map exposes read-only `.count` of type `Int`.

### Value semantics

Maps are ordinary values. Assignment/copying creates an independent logical value:

```eri
let first be ["a" : 1;];
let second be first;
second["a"] = 2;

output(first["a"]);  // 1
output(second["a"]); // 2
```

Implementations may use copy-on-write, hashing, shared immutable backing storage or other optimizations as long as this observable value behavior is preserved.

### Order and equality

Map equality is based on key/value correspondence, not entry position. Two Maps compare equal when they contain the same keys and each key maps to an equal value.

The initial implementation preserves insertion order for deterministic diagnostics/output, but source programs must not depend on Map traversal order because direct Map `for` iteration is not part of the initial contract.

A native implementation should use associative lookup appropriate to production workloads; the source semantics do not require a particular hash-table representation.

## 4. Bytes

`Bytes` is a compact binary value, not an alias for `List<Int>`.

The same bracket syntax is reused because the expected type already makes the intent unambiguous:

```eri
let data Bytes be [72, 101, 108, 108, 111];
```

Without Bytes context, the same literal remains a normal List of Int:

```eri
let numbers be [72, 101, 108]; // List of Int
```

Eristavi never guesses Bytes merely because every integer happens to fit in a byte.

### Bytes context

Bytes context may come from:

- an explicit `Bytes` binding annotation;
- a `Bytes` function parameter;
- a `Bytes` return contract;
- assignment where the destination is already statically `Bytes`.

Examples:

```eri
function first(data Bytes) returns Int {
    return data[0];
}

output(first([65, 66]));
```

```eri
function greeting() returns Bytes {
    return [72, 105];
}
```

### Element range

Each Bytes element has semantic type `Int` and must satisfy:

```text
0 <= value <= 255
```

An out-of-range constant is rejected at compile time. A nonconstant value that violates the range during mutation/construction produces a defined runtime fault.

### Indexing, mutation and count

Bytes uses zero-based checked indexing:

```eri
let data Bytes be [72, 101];
output(data[1]); // 101
data[1] = 97;
```

Reading an element produces `Int`.

Every Bytes value exposes read-only `.count` of type `Int`.

### Representation

A conforming implementation may store `Bytes` as compact contiguous octets. It must not be forced to represent each byte as a full general-purpose Eristavi `Int` value.

This distinction matters for files, networking, encoding, cryptography and binary protocols.

### Value semantics and equality

Bytes is an ordinary value. Copies are logically independent under mutation.

Equality is byte-for-byte and order-sensitive.

## 5. `fixed`

The existing deep-fixable rule applies to collections.

A fixed List, Map or Bytes value cannot be mutated through that binding.

For Maps and Lists, nested ordinary values must also satisfy the existing deep-fixable contract. Reachable identity/resource state prevents a deep `fixed` guarantee where the existing language rules already prohibit it.

## 6. Output

`output(...)` may display collection values using their canonical surface structure when their nested values are outputable.

Examples:

```text
[1, 2, 3]
[72, 101, 108]
["Anna" : 32; "John" : 41;]
```

Text values nested inside a collection are quoted/escaped so structure remains unambiguous.

Bytes output uses decimal byte values by default. Hexadecimal formatting is an explicit formatting concern rather than alternate Bytes semantics.

## 7. Deliberately postponed collection families

The core language does not need separate built-in syntax or compiler machinery for:

- `Set`;
- stack;
- queue/deque;
- priority queue;
- ordered/sorted Map variants;
- multi-map;
- linked list;
- lazy sequence;
- comprehensions;
- parallel collection operations.

These can be standard-library abstractions built from the fundamental runtime capabilities when real programs justify them.

`Stack` in particular does not need to duplicate ordinary List behavior merely to add another name.

## 8. Diagnostics

Useful diagnostics include:

- mixed incompatible List element types;
- unresolved empty-List element relationship;
- mixed incompatible Map key/value relationships;
- unresolved empty-Map key/value relationships;
- unsupported Map key type;
- duplicate statically obvious Map key;
- nonmatching Map lookup key;
- non-`Int` List/Bytes index;
- statically provable out-of-range List/Bytes index or byte value;
- incompatible indexed assignment;
- mutation through a fixed collection;
- equality on a collection whose nested relationships are not equality-comparable.

Diagnostics should name the relevant relationship rather than collapsing these cases into a generic type failure.

## Governing principle

> Eristavi has a small collection foundation with one obvious notation: comma-separated `[]` for ordered sequences, `key : value;` entries inside `[]` for associative Maps, and the same sequence literal interpreted as `Bytes` only when static Bytes context makes that intent explicit. The types remain strong and distinct even when the syntax is shared.
