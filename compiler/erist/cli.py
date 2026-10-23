from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .diagnostics import EristaviError
from .lexer import Lexer
from .parser import Parser
from .runtime import Interpreter
from .semantic import Analyzer


def compile_frontend(source: str):
    tokens = Lexer(source).lex()
    program = Parser(tokens).parse()
    Analyzer().analyze(program)
    return program


def run_file(path: Path) -> int:
    try:
        source = path.read_text(encoding="utf-8")
        program = compile_frontend(source)
        Interpreter().run(program)
        return 0
    except EristaviError as exc:
        print(exc.format(), file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def check_file(path: Path) -> int:
    try:
        source = path.read_text(encoding="utf-8")
        compile_frontend(source)
        return 0
    except EristaviError as exc:
        print(exc.format(), file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="erist", description="Eristavi bootstrap toolchain")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run an Eristavi entry source file using the bootstrap execution backend")
    run.add_argument("entry", type=Path)

    check = sub.add_parser("check", help="lex, parse, and type-check an Eristavi source file")
    check.add_argument("entry", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "run":
        return run_file(args.entry)
    if args.command == "check":
        return check_file(args.entry)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
