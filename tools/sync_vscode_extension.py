from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
PAIRS = (
    (
        ROOT / "syntax" / "eristavi.tmLanguage.json",
        ROOT / "editors" / "vscode" / "syntaxes" / "eristavi.tmLanguage.json",
    ),
    (
        ROOT / "syntax" / "language-configuration.json",
        ROOT / "editors" / "vscode" / "language-configuration.json",
    ),
    (
        ROOT / "LICENSE",
        ROOT / "editors" / "vscode" / "LICENSE",
    ),
)


def main():
    for source, target in PAIRS:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        print(f"synced {source.relative_to(ROOT)} -> {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
