# Eristavi Module Interfaces and Implementation Artifacts

> **Status: Versioned interface, Universal-IR objects, reusable inferred-generic templates, and incremental artifact caching implemented**

Eristavi separates reusable module contracts from reusable implementation artifacts.

```text
module.eri
  ├─→ erist interface → module.eri-interface.json
  └─→ erist object    → module.eri-object.json
```

An importer can type-check from the interface without dependency source. The direct compiler can link implementations from the interface + object pair after the dependency `.eri` file has been removed.

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
- public type/error field metadata;
- public function contracts;
- inferred generic relationships and operation constraints;
- return relationships;
- checked `fails` contracts.

Serialization is deterministic canonical JSON and has a SHA-256 digest.

Private functions are not exposed as callable interface symbols. Structural metadata required to validate public contracts may remain compiler-visible without becoming source-addressable.

## Implementation object

Current implementation artifact format:

```text
schema  = eristavi.module-object
version = 3
IR      = universal-ir-v3
```

It records:

- module identity;
- the exact interface digest it was compiled against;
- dependency identities;
- concrete verified/optimized Universal-IR functions;
- nominal/error layouts required by those functions;
- checked-failure contracts;
- when needed, a bootstrap reusable inferred-generic implementation template.

The linker rejects interface/object digest mismatches.

## Source-independent executable linkage

Verified workflow:

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
direct executable
```

Tests cover scalar functions, nominal parameters/returns, List returns, checked-error contracts, public type construction and private-function isolation.

## Inferred generics after source removal

The interface preserves inferred relationships without adding source generic syntax. For example:

```eri
public function preserve(value) {
    return value;
}
```

exposes a compiler relationship equivalent to:

```text
(T0) -> T0
```

Object v3 can carry a bootstrap implementation template for modules exporting inferred-generic functions. A downstream concrete call can therefore request a specialization after the original dependency `.eri` file has been removed.

Current v3 bootstrap representation uses:

```text
generic_template.kind = eristavi-source-v1
```

The serialized template is implementation material, not user-written generic syntax. It is re-analyzed against the serialized module/dependency contracts, specialized to the downstream concrete argument types, lowered to Universal IR and linked with the object's already-concrete functions.

Tests cover post-source-removal specialization of:

- identity/preserve-style relationships;
- same-type multi-parameter relationships;
- List element relationships.

A future compact binary/template IR may replace the bootstrap source-template payload without changing Eristavi source semantics.

## Incremental artifact caching

`erist compile-module` builds reusable interface/object artifacts through a content/interface-digest keyed cache.

The cache contract is intentionally semantic:

- changing a module's own source invalidates its own key;
- changing a dependency's public interface invalidates importers;
- changing only a dependency's private implementation does not invalidate an importer whose dependency contract digest is unchanged;
- an identical second compile is a cache hit.

This is bootstrap incremental compilation rather than a full production package/build graph, but it establishes the correct contract boundary.

## Artifact evolution

JSON remains a bootstrap interchange format. Later releases may use compact binary artifacts, platform-specific object containers or a richer linker index. Any replacement must remain versioned and preserve:

- interface/implementation separation;
- Unicode/toolchain compatibility checks;
- dependency contract identities;
- reproducible specialization behavior;
- semantic validation before linking.
