# Eristavi Language Support for VS Code

Official syntax-highlighting support for the Eristavi programming language.

## Features

- recognizes `.eri` source files as Eristavi;
- uses the canonical `source.eristavi` TextMate grammar;
- highlights Eristavi declarations, control flow, checked errors, resources, imports, built-in types, literals, operators and function calls;
- supports Eristavi line comments and nestable block-comment highlighting;
- provides bracket, quote and comment-pair configuration;
- works as a declarative extension with no extension-host JavaScript runtime.

The source-language contract remains defined by the Eristavi specification in the main repository. This extension does not introduce syntax or aliases that are not part of Eristavi.

## Install a local VSIX

From this directory:

```sh
npx @vscode/vsce package
```

Then install the generated package:

```sh
code --install-extension eristavi-language-0.0.1.vsix
```

You can also use **Extensions: Install from VSIX...** from the VS Code command palette.

## Canonical grammar

The canonical grammar lives at:

```text
../../syntax/eristavi.tmLanguage.json
```

The copy under `syntaxes/` is the packaging mirror used by the VS Code extension. Repository tests require it to remain byte-for-byte identical to the canonical grammar. The same rule applies to `language-configuration.json`.

When the canonical syntax files change, run:

```sh
python tools/sync_vscode_extension.py
```

from the repository root before committing.

## Marketplace publishing

The extension manifest uses the publisher identifier `eristavi`. The publisher must exist and be controlled by the project before Marketplace publication.

Project: https://eristavi.org

Repository: https://github.com/eristavi/eristavi-lang

## License

MIT
