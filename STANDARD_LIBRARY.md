# Eristavi Standard Library

> **Status: Small bootstrap surface; library-first expansion**

Eristavi keeps language syntax deliberately small and grows practical capability through standard modules.

## Prelude

`output(value)` is available without an import. It is a predeclared standard function, not a keyword.

## `std.files`

The implemented file module currently provides deterministic resource I/O plus checked path operations.

### `files.open(path)`

Returns a deterministic file resource and may fail with `files.FileError`.

```eri
import std.files;

with file be try files.open("data.txt") {
    let text be try file.readText();
    output(text);
}
```

The file resource currently exposes:

```text
file.readText()
file.writeText(text)
```

Text reads validate UTF-8. Invalid UTF-8 is a checked `FileError`; arbitrary bytes do not silently become `Text`.

### `files.exists(path)`

Checks whether a filesystem path exists:

```eri
import std.files;

function exists(path Text) returns Bool fails files.FileError {
    return try files.exists(path);
}
```

A nonexistent path yields `false`. Invalid paths and operating-system errors remain checked `FileError` failures rather than being collapsed into `false`.

### `files.remove(path)`

Removes a filesystem entry and may fail with `files.FileError`:

```eri
import std.files;

function remove(path Text) fails files.FileError {
    try files.remove(path);
}
```

A missing target is a checked failure rather than silent success.

## Path/Text boundary

Filesystem APIs accept Eristavi `Text`. When a host API requires a NUL-terminated path, an embedded NUL is rejected through the checked file-error channel rather than silently truncating the path.

## Direction

Future library work should usually add modules/functions rather than keywords. Likely domains include:

- paths;
- JSON/data encoding;
- time;
- networking;
- process/environment APIs;
- richer numeric utilities.

Those additions should preserve the same rule used by the current file module: host APIs implement Eristavi contracts; platform accidents do not redefine them.

## `std.unicode`

A small pinned Unicode **17.0.0** library supports the compiler migration and
ordinary Text processing without adding keywords or implicit normalization:

| Function | Input | Result | Contract |
| --- | --- | --- | --- |
| `unicode.isIdentifierStart(scalar)` | `Text` | `Bool` | One scalar satisfying XID_Start, or underscore. |
| `unicode.isIdentifierContinue(scalar)` | `Text` | `Bool` | One scalar satisfying XID_Continue, or underscore. |
| `unicode.normalizeNfc(text)` | `Text` | `Text` | Explicit NFC normalization; ordinary Text is not normalized implicitly. |
| `unicode.fromScalar(code)` | `Int` | `Text` | One Unicode scalar; invalid scalar integers produce a defined runtime fault. |

Empty or multi-scalar Text yields `false` for either identifier predicate.
`fromScalar` accepts U+0000 through U+10FFFF excluding surrogates U+D800–U+DFFF.
Embedded NUL remains part of Text and is never treated as a terminator.

```eri
import std.unicode;
output(unicode.normalizeNfc("A\u{301}"));
output(unicode.fromScalar(128512));
```

Current execution support: reference runtime and generated-C backend (`erist build`).
The C executable embeds pinned tables and has no Python/ICU/locale dependency at
runtime. Direct native, JavaScript and Wasm implementations of this library are
pending and reject its use explicitly. Existing target capabilities are unchanged.
