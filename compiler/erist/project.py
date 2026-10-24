from __future__ import annotations

from .stdlib import BUILTIN_MODULES

from dataclasses import dataclass
from pathlib import Path

from .diagnostics import SemanticError
from .interface import InterfaceAnalyzerProxy, ModuleInterface
from .lexer import Lexer
from .parser import Parser
from .semantic_ext import Analyzer
from .syntax import ImportDecl


@dataclass
class CompiledModule:
    path: tuple[str, ...]
    module_id: str
    file_path: Path
    program: object | None
    analyzer: object
    imports: dict[str, "CompiledModule"]
    interface: ModuleInterface
    interface_only: bool = False


class ProjectCompiler:
    def __init__(self, source_root: Path):
        self.root = source_root.resolve()
        self.cache: dict[tuple[str, ...], CompiledModule] = {}
        self.loading: list[tuple[str, ...]] = []

    @staticmethod
    def interface_path(source_path: Path) -> Path:
        return source_path.with_suffix(".eri-interface.json")

    def _logical_for(self, path: Path) -> tuple[str, ...]:
        path = path.resolve()
        try:
            rel = path.relative_to(self.root)
        except ValueError:
            raise SemanticError("module file must be inside the configured source root")
        # Interface paths are never passed here; logical names come from .eri paths.
        return tuple(rel.with_suffix("").parts)

    def compile_entry(self, entry: Path) -> CompiledModule:
        entry = entry.resolve()
        return self._load(self._logical_for(entry), entry, True)

    def compile_module(self, module: Path) -> CompiledModule:
        module = module.resolve()
        return self._load(self._logical_for(module), module, False)

    def _load(self, logical: tuple[str, ...], file_path: Path, is_entry: bool) -> CompiledModule:
        if logical in self.cache:
            mod = self.cache[logical]
            if is_entry and mod.interface_only:
                raise SemanticError("an interface-only module cannot be selected as an executable entry")
            return mod
        if logical in self.loading:
            cycle = " -> ".join(".".join(x) for x in self.loading + [logical])
            raise SemanticError(f"circular module dependency: {cycle}")

        self.loading.append(logical)
        try:
            if file_path.exists():
                return self._load_source(logical, file_path, is_entry)
            interface_path = self.interface_path(file_path)
            if interface_path.exists():
                if is_entry:
                    raise SemanticError("an interface-only module cannot be selected as an executable entry")
                return self._load_interface(logical, file_path, interface_path)
            raise SemanticError(f"cannot resolve module {'.'.join(logical)!r}")
        finally:
            self.loading.pop()

    def _load_source(self, logical: tuple[str, ...], file_path: Path, is_entry: bool) -> CompiledModule:
        source = file_path.read_text(encoding="utf-8")
        program = Parser(Lexer(source).lex()).parse()
        imports: dict[str, CompiledModule] = {}
        for stmt in program.statements:
            if not isinstance(stmt, ImportDecl) or stmt.path in BUILTIN_MODULES:
                continue
            target = self.root.joinpath(*stmt.path).with_suffix(".eri")
            alias = stmt.alias or stmt.path[-1]
            imports[alias] = self._load(stmt.path, target, False)

        module_id = ".".join(logical)
        analyzer = Analyzer(module_id, imports, is_entry)
        analyzer.analyze(program)
        interface = ModuleInterface.from_analyzer(module_id, analyzer)
        mod = CompiledModule(logical, module_id, file_path, program, analyzer, imports, interface, False)
        self.cache[logical] = mod
        return mod

    def _load_interface(self, logical: tuple[str, ...], source_path: Path, interface_path: Path) -> CompiledModule:
        try:
            interface = ModuleInterface.from_json(interface_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise SemanticError(f"cannot read interface for {'.'.join(logical)!r}: {exc}")
        expected = ".".join(logical)
        if interface.module_id != expected:
            raise SemanticError(
                f"interface module id mismatch: expected {expected!r}, found {interface.module_id!r}"
            )

        dependencies: dict[str, CompiledModule] = {}
        for dependency in interface.dependencies:
            path = tuple(part for part in dependency.split(".") if part)
            if not path:
                raise SemanticError(f"interface {expected!r} contains an invalid dependency name")
            target = self.root.joinpath(*path).with_suffix(".eri")
            dependencies[dependency] = self._load(path, target, False)

        analyzer = InterfaceAnalyzerProxy(interface)
        # Imported contracts may contain public value fields whose canonical type
        # is owned by another module.  Merge dependency structure metadata for
        # deep-fixed/equality checks without exposing dependency-local source names.
        for dependency in dependencies.values():
            analyzer.structs.update(dependency.analyzer.structs)
        mod = CompiledModule(logical, expected, source_path, None, analyzer, dependencies, interface, True)
        self.cache[logical] = mod
        return mod


def compile_entry(path: Path, source_root: Path | None = None) -> CompiledModule:
    path = path.resolve()
    root = (source_root or path.parent).resolve()
    return ProjectCompiler(root).compile_entry(path)


def compile_module(path: Path, source_root: Path | None = None) -> CompiledModule:
    path = path.resolve()
    root = (source_root or path.parent).resolve()
    return ProjectCompiler(root).compile_module(path)
