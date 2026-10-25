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

## Frontend bootstrap I/O

These additions currently execute in the reference runtime and C backend. Other
backends reject their use with guidance to use `erist build`.

### `files.openRead(path)`

Opens an existing file for UTF-8 reading without requiring write permission.
The returned `files.File` is owned by `with` and uses the existing cleanup and
checked `files.FileError` contract. Attempting `writeText` on a read-only resource
is a checked error and does not modify the input. Reads preserve CR/LF scalars.

### `files.create(path)`

Exclusively creates a new UTF-8 file and returns a writable scoped `files.File`.
An existing path, including a symlink, causes checked `files.FileError`; it is not
truncated. `writeText` and `readText` use the existing file-resource contract.
Embedded NUL paths and OS acquisition errors are checked file failures. Contents
can contain embedded NUL. This is not an atomic file-replacement operation.

## `std.process`

| Function | Result | Contract |
| --- | --- | --- |
| `process.arguments()` | inferred List of Text | A value snapshot of arguments, excluding the executable name. Empty values and ordering are preserved. Invalid UTF-8 produces a defined runtime fault. |
| `process.writeError(text)` | no value | Writes Text followed by a newline to stderr. |
| `process.setExitCode(code)` | no value | Sets the eventual entry exit status to an Int from 0 through 255. Out-of-range values produce a defined runtime fault. |

`setExitCode` does not terminate execution. Ordinary return and checked-failure
cleanup continue to release scoped resources. Imported modules share the same
process state; modifying an argument List does not modify the stored arguments.
The default exit status is zero. A runtime fault or unhandled failure still exits
with failure according to the existing runtime contract.

The reference CLI forwards arguments with `erist run SOURCE.eri -- ARGUMENTS`.
These functions are library operations; Eristavi's implicit entry body and frozen
keyword set are unchanged.

### `files.canonicalPath(path)`

Returns the canonical absolute Text path of an existing filesystem entry, resolving
symbolic links and relative segments. Missing entries, embedded NUL and OS failures
use checked `files.FileError`. This supports source-root identity in the semantic
module loader without adding path syntax. Execution support is currently the
reference/C route, verified on hosted Linux/macOS. Other backends reject the new
operation explicitly, as with `openRead` and `create`.
