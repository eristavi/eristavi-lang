# Eristavi Collections

> **Status: Locked for pre-0.1**

This document defines the first concrete Eristavi collection model.

The governing rule is:

> Pre-0.1 has one ordinary ordered growable collection family: `List`. Its element relationship is statically inferred, indexing is zero-based and checked, mutation follows ordinary value semantics, and advanced collection families remain library/future work.

## 1. One default collection family

The canonical pre-0.1 collection family is `List`.

A list is:

- ordered;
- growable;
- homogeneous in its static element relationship;
- an ordinary Eristavi value rather than shared identity by default.

List literals use the already-locked bracket syntax:

```eri
let names be ["Anna", "Maria", "John"];
```

The compiler infers that `names` is a List whose element type is `Text`.

Pre-0.1 does not introduce separate `Array`, `Vector`, `Sequence`, or linked-list language concepts merely to offer several names for the same everyday collection role.

## 2. `List` is not a keyword

`List` is a predeclared type-family name, not a reserved lexical keyword.

The element type remains statically known to the compiler, but pre-0.1 still exposes no user-written generic argument syntax.

Therefore this is not pre-0.1 Eristavi source syntax:

```text
List<Text>
List[Int]
List[User]
```

A bare `List` is not a complete explicit value-type annotation because the element relationship must be known. Ordinary pre-0.1 code obtains that relationship through inference from literals, use, parameters, return context, or other statically analyzable constraints.

The compiler/tooling may describe the inferred type in diagnostics using human-readable wording such as "List of Text" without making that wording source syntax.

## 3. Homogeneous element relationship

A List has one statically coherent element type.

Valid:

```eri
let numbers be [1, 2, 3];
let names be ["Anna", "Maria"];
```

Invalid:

```eri
let mixed be [1, "one"];
```

Eristavi does not silently widen a mixed list to `dynamic`, `Any`, an implicit union, or another catch-all type.

The existing no-implicit-lossy-conversion rules also apply. For example, `Int` and `Float` are not silently mixed by converting one to the other:

```eri
let values be [1, 2.0]; // compile-time error
```

## 4. Empty List inference

An empty literal is valid only when the compiler can establish its element relationship from static context.

For example:

```eri
let customers be [];

customers.add(Customer {
    name = "Anna";
});
```

may establish that `customers` is a List of `Customer` when the complete statically analyzable use makes that relationship unambiguous.

Context may also come from a function parameter, return contract/inference relationship, assignment, or another ordinary static constraint.

If the compiler cannot determine one element type, compilation fails rather than creating an untyped or dynamically typed List.

```eri
let items be []; // error when no later/contextual constraint establishes the element type
```

Conflicting constraints are likewise compile-time errors.

## 5. Zero-based indexing

List indexing is zero-based.

```eri
let names be ["Anna", "Maria", "John"];

output(names[0]); // Anna
output(names[1]); // Maria
```

The index expression must have static type `Int`.

For a List with `count` elements, valid indexes satisfy:

```text
0 <= index < count
```

Negative indexing does not mean "from the end" in pre-0.1. A negative index is out of bounds.

## 6. Bounds behavior

Indexing is checked.

If an index is provably out of range at compile time, the compiler should reject the program with a clear diagnostic.

Otherwise, an out-of-range access produces a defined runtime bounds fault.

A bounds fault is a runtime defect, not an ordinary checked `fails` value, matching the existing distinction used for arithmetic defects such as integer division by zero.

Indexing does not silently clamp, wrap, return `none`, or choose another fallback behavior.

A future safe lookup library API may return `maybe T` if real programs need that operation, but it is not alternate indexing syntax.

## 7. Reading elements

Reading:

```eri
let first be items[0];
```

produces the element according to its normal Eristavi semantics.

For an ordinary value element, the result behaves as an ordinary independent logical value.

For an `identity T` element, reading the element produces the same logical identity handle, because identity assignment/copying preserves identity.

No separate reference-to-element concept is exposed in pre-0.1.

## 8. Indexed mutation

A mutable List supports indexed assignment:

```eri
let numbers be [10, 20, 30];
numbers[1] = 25;
```

The assigned value must be compatible with the List's inferred element type.

Indexed paths may participate in ordinary nested mutation where the complete path is mutable:

```eri
users[0].name = "Maria";
```

This updates the stored ordinary value while preserving Eristavi value semantics. The compiler/runtime may implement the operation through in-place optimization, copy-on-write, reconstruction, or another mechanism as long as observable behavior is the same.

Conceptually, assignment targets may therefore contain member and index path segments. This extends the assignment-target semantic model without making `=` an expression operator.

## 9. `.count`

Every List exposes a read-only `count` property of type `Int`:

```eri
let names be ["Anna", "Maria"];
output(names.count); // 2
```

`count` is the number of elements currently stored in the List.

It is not assignable:

```eri
names.count = 10; // compile-time error
```

Pre-0.1 uses `count` rather than introducing synonymous `length` / `size` properties for the same concept.

## 10. `.add(value)`

A mutable List supports one canonical append operation:

```eri
names.add("John");
```

`add(value)` appends the value to the end of the List.

The value must be compatible with the List's element type.

`add` is a no-value operation in pre-0.1; it does not return the inserted element, the index, or the List.

This keeps mutation explicit and prevents chaining from creating a second implicit collection-building model.

## 11. Value semantics

A List is an ordinary Eristavi value by default.

```eri
let first be [1, 2];
let second be first;

second.add(3);

output(first.count);  // 2
output(second.count); // 3
```

Mutating `second` must not mutate `first`.

The compiler/runtime may use copy-on-write, shared backing storage, move optimization, escape analysis, or other representation techniques as long as observable List behavior remains value-based.

Passing a List as an ordinary function parameter follows the same value-parameter rule: mutations to the parameter's List value do not mutate the caller-owned ordinary List.

Shared mutable List state requires explicit identity at a containing semantic boundary rather than hidden aliasing.

## 12. `fixed` Lists

`fixed` applies deeply to Lists under the already-locked deep-fixable rule.

```eri
let fixed names be ["Anna", "Maria"];
```

For such a List:

```eri
names.add("John"); // compile-time error
names[0] = "Ana"; // compile-time error
```

The List's nested ordinary values are likewise immutable through the fixed value.

A List whose element type contains `identity` at a reachable stored position is not deep-fixable and therefore cannot receive a `fixed` guarantee.

## 13. Equality

The already-locked ordinary value equality model applies.

Two Lists are equal when:

1. they contain the same number of elements; and
2. every corresponding element compares equal using the element type's own equality semantics.

Order matters:

```eri
[1, 2, 3] == [1, 2, 3] // true
[1, 2, 3] == [3, 2, 1] // false
```

A List is equality-comparable only when its element type is equality-comparable.

## 14. `for` iteration

`for` iterates List elements from index `0` upward in stored order.

```eri
for name in names {
    output(name);
}
```

The loop observes the logical List value present when iteration begins. Subsequent mutation of the source does not alter which element sequence that active loop is traversing.

This is a semantic snapshot, not a requirement that the runtime eagerly copy the entire List. The compiler/runtime may implement stable iteration more efficiently as long as the observable sequence is unchanged.

Each loop binding receives the element according to ordinary value/identity semantics.

## 15. Deliberately postponed operations

Pre-0.1 does not need dedicated core semantics for:

- slicing;
- ranges;
- negative/from-end indexing;
- insertion at arbitrary positions;
- removal APIs;
- sorting APIs;
- maps/dictionaries;
- sets;
- queues/deques;
- linked lists;
- lazy sequences;
- comprehensions;
- parallel collection operations.

These may be added through the standard library or later language/library design when real programs demonstrate the need.

Their absence does not prevent implementations from providing ordinary library functions that operate on Lists where consistent with the frozen semantics.

## 16. Diagnostics

Useful compiler diagnostics include:

- mixed incompatible element types;
- unresolved empty-List element type;
- conflicting inferred element constraints;
- non-`Int` index;
- statically provable out-of-range index;
- assignment of an incompatible element type;
- mutation of a fixed List;
- use of equality when the element type is not equality-comparable.

Diagnostics should identify the relevant element type or index constraint rather than reporting only a generic type error.

## Governing principle

> A List is one predictable ordered growable value: infer one element type, index from zero with checked bounds, use `count` for element count, `add` for append, preserve value semantics, and postpone additional collection families until they solve demonstrated problems.
