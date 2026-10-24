# Eristavi Module Interfaces and Implementation Artifacts

> **Status: Versioned interface and concrete Universal-IR object formats implemented**

Eristavi now separates reusable module contracts from reusable implementation artifacts.

```text
module.eri
  ├─→ erist interface → module.eri-interface.json
  └─→ erist object    → module.eri-object.json
```

An importer can type-check from the interface without the dependency source. The direct compiler can also link supported concrete implementations from the interface + object pair after the dependency `.eri` source has been removed.

## Public interface artifact

Current interface format:

```text
schema  = eristavi.module-interface
version = 1
```

It records:

- canonical module identity;
- pinned Unicode version;
- dependency identities;
- type/error field metadata required for static semantics;
- public visibility;
- public function contracts;
- inferred generic relationships and operation constraints;
- return relationships;
- checked `fails` contracts.

Serialization is deterministic canonical JSON and has a SHA-256 digest.

Private functions are not exposed as callable interface symbols. Structural metadata needed to validate public contracts may remain available to the compiler without making private declarations source-addressable.

## Concrete implementation object

Current implementation artifact format:

```text
schema  = eristavi.module-object
version = 2
IR      = universal-ir-v2
```

It records:

- module identity;
- the exact interface digest it was compiled against;
- dependency identities;
- concrete Universal-IR functions;
- nominal/error layouts required by those functions;
- checked-failure contracts.

The linker rejects an object if its embedded interface digest does not match the interface currently used by the importer.

## Source-independent executable linkage

This workflow is verified:

```text
lib.eri
   ↓
interface + object
   ↓
delete lib.eri
   ↓
compile app.eri importing lib
   ↓
link serialized Universal IR
   ↓
direct x86-64 executable
```

Tests cover scalar functions, nominal value parameters/returns, List returns, checked-error contracts, public type construction, and private-function isolation.

## Inferred generics

The interface format preserves inferred generic relationships without adding generic syntax to Eristavi source. For example:

```eri
public function preserve(value) {
    return value;
}
```

can expose the compiler relationship:

```text
(T0) -> T0
```

Source builds already monomorphize inferred generic functions through the direct backend.

A remaining object-artifact boundary is **reusable generic implementation templates**. A precompiled interface-only module can expose an inferred generic contract, but its object artifact does not yet carry a generic implementation template that can be specialized at an arbitrary downstream call site. That is an implementation-artifact problem, not a source-language design gap.

## Artifact evolution

The JSON encodings are bootstrap interchange formats. They may later become compact binary artifacts, caches, or platform-specific object containers. Any replacement must remain versioned and must preserve the contract/implementation separation and semantic validation currently provided by the interface digest.
