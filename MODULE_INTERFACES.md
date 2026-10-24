# Eristavi Module Interfaces

> **Status: Implemented bootstrap interface format**

Eristavi now has a serialized module-contract boundary independent of live Python analyzer objects.

## Purpose

A reusable module can emit a deterministic interface artifact:

```text
models/user.eri
      ↓
erist interface
      ↓
models/user.eri-interface.json
```

An importing module can type-check against that artifact even when the imported `.eri` source is unavailable.

This separates **public contract information** from implementation bodies and private callable names.

## Current format

The bootstrap artifact is versioned:

```text
schema  = eristavi.module-interface
version = 1
```

It records:

- canonical module identity;
- pinned Unicode version;
- dependency module identities;
- user-defined type/error field layouts required for static semantics;
- public/private visibility of type declarations;
- public function parameter relationships;
- inferred generic type variables and operation constraints;
- return-type relationships;
- checked `fails` contracts.

Serialization is deterministic JSON and the compiler can compute a SHA-256 digest of the canonical serialized form.

The JSON representation is a bootstrap interchange format. A future compact/binary encoding may replace it without changing Eristavi source semantics, provided the versioned contract remains explicit.

## Visibility

For a module such as:

```eri
public type User {
    fixed id Int;
    name Text;
}

function internalLookup(id Int) returns User {
    // ...
}

public function preserve(value) {
    return value;
}
```

The interface makes `User` and `preserve` available to importers. `internalLookup` is not exported as a callable symbol.

Private structural type metadata may still be present when required to prove transitive compiler properties such as equality-comparability or deep-fixability of a public contract; this does not make the private declaration source-addressable.

## Inferred generics

Eristavi does not expose generic type-variable syntax in pre-0.1, but module interfaces must preserve the relationships inferred by the compiler.

Conceptually:

```eri
public function preserve(value) {
    return value;
}
```

exports the relationship:

```text
(T0) -> T0
```

The `T0` name is interface/compiler metadata, not Eristavi source syntax.

## Current executable boundary

Interface-only imports are sufficient for frontend type checking.

They are **not yet object-code artifacts**. `erist run`, the generated-C executable path, and the direct CPU executable path still require implementation source for linked executable modules.

That distinction is intentional:

```text
interface artifact → type-check contract
implementation IR/object artifact → executable linkage   (future)
```

The next module-artifact step is to pair the interface with compiled implementation/object metadata rather than expanding the source language.
