"""Execute compiler components as ordinary Eristavi modules."""
from pathlib import Path
import shutil
from compiler.erist.project import compile_entry
from compiler.erist.runtime_ext import Interpreter

SELFHOST_ROOT = Path(__file__).resolve().parents[1] / "src"


def literal(text):
    # Encode payloads using Eristavi escapes, including BOMs and control scalars.
    return '"' + ''.join(
        '\\u{%X}' % ord(ch) if ord(ch) < 32 or ord(ch) >= 127 or ch in '\\"' else ch
        for ch in text
    ) + '"'


def prepare(root, source):
    shutil.copytree(SELFHOST_ROOT / "compiler", root / "compiler", dirs_exist_ok=True)
    entry = root / "probe.eri"
    entry.write_text(source, encoding="utf-8")
    return entry


def execute(entry, root):
    module = compile_entry(entry, root)
    output = []
    Interpreter(output.append, module.module_id, module.imports).run(module.program)
    return output
