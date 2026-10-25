# Eristavi syntax support

This directory contains the canonical TextMate-compatible grammar and editor language configuration for Eristavi source files (`.eri`).

- `eristavi.tmLanguage.json` — TextMate grammar with scope `source.eristavi`.
- `language-configuration.json` — editor metadata for comments, brackets and auto-closing pairs.

The grammar is intended to be reusable by VS Code-compatible editors and as the upstream grammar reference for a future GitHub Linguist submission. It must follow the frozen Eristavi grammar and semantics rather than introducing editor-only syntax.
