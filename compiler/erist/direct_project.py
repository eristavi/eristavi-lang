from __future__ import annotations

from .stdlib import BUILTIN_MODULES

from dataclasses import fields, is_dataclass
from pathlib import Path

from .ir import IRCall, IRProgram, Lowerer as CoreLowerer
from .ir_text import Lowerer
from .lexer import Lexer
from .object_artifact import ModuleObjectArtifact
from .parser import Parser
from .project import CompiledModule, compile_entry, compile_module
from .semantic_ext import Analyzer
from .syntax import ImportDecl
from .universal_ir import UProgram
from .universal_passes import optimize_program
from .universal_resources import ResourceUniversalLowerer


def object_path(source_path: Path) -> Path:
    return source_path.with_suffix(".eri-object.json")


def _ordered(root: CompiledModule, *, allow_interfaces: bool) -> tuple[list[CompiledModule], list[CompiledModule]]:
    source: list[CompiledModule] = []
    interface_only: list[CompiledModule] = []
    seen: set[str] = set()

    def visit(mod: CompiledModule) -> None:
        if mod.module_id in seen:
            return
        seen.add(mod.module_id)
        for child in mod.imports.values():
            visit(child)
        if mod.interface_only:
            if not allow_interfaces:
                raise ValueError(
                    f"module {mod.module_id!r} is interface-only; compile its implementation artifact first"
                )
            interface_only.append(mod)
        else:
            source.append(mod)

    visit(root)
    return source, interface_only


def _module_registry(root: CompiledModule) -> dict[str, CompiledModule]:
    result = {}
    seen = set()
    def visit(mod):
        if mod.module_id in seen:
            return
        seen.add(mod.module_id)
        result[mod.module_id] = mod
        for child in mod.imports.values():
            visit(child)
    visit(root)
    return result


def typed_source_project(root: CompiledModule, *, allow_interfaces: bool) -> tuple[IRProgram, list[CompiledModule]]:
    source, interfaces = _ordered(root, allow_interfaces=allow_interfaces)
    structs = []
    functions = []
    entry = []
    for mod in source:
        include_entry = mod is root
        part = Lowerer(mod.analyzer, mod.module_id).lower(mod.program, include_entry)
        structs.extend(part.structs)
        functions.extend(part.functions)
        if include_entry:
            entry.extend(part.entry)
    return IRProgram(structs, functions, entry), interfaces


def compile_module_object(path: Path, source_root: Path | None = None) -> ModuleObjectArtifact:
    mod = compile_module(path, source_root)
    if mod.interface_only:
        raise ValueError("cannot compile an implementation artifact without module source")
    typed, _ = typed_source_project(mod, allow_interfaces=False)
    universal = optimize_program(ResourceUniversalLowerer().lower(typed))
    prefix = mod.module_id + "."
    own_functions = tuple(fn for fn in universal.functions if fn.name.startswith(prefix))
    own_types = tuple(item for item in universal.types if item.name.startswith(prefix))
    has_public_generic = any(
        fn.declaration.public and any(param.type_annotation is None for param in fn.declaration.parameters)
        for fn in mod.analyzer.functions.values()
    )
    generic_source = path.read_text(encoding="utf-8") if has_public_generic else None
    return ModuleObjectArtifact(
        mod.module_id,
        mod.interface.digest,
        mod.interface.dependencies,
        own_functions,
        own_types,
        generic_source,
    )


def _load_object(mod: CompiledModule) -> ModuleObjectArtifact:
    path = object_path(mod.file_path)
    if not path.exists():
        raise ValueError(
            f"module {mod.module_id!r} has an interface but no implementation artifact {path.name!r}"
        )
    artifact = ModuleObjectArtifact.from_json(path.read_text(encoding="utf-8"))
    if artifact.module_id != mod.module_id:
        raise ValueError(
            f"module object id mismatch: expected {mod.module_id!r}, found {artifact.module_id!r}"
        )
    if artifact.interface_digest != mod.interface.digest:
        raise ValueError(
            f"module object for {mod.module_id!r} was built against a different public interface"
        )
    return artifact


def _walk_calls(value):
    if isinstance(value, IRCall):
        yield value
    if is_dataclass(value):
        for field in fields(value):
            yield from _walk_calls(getattr(value, field.name))
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_calls(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk_calls(item)


def _template_module(artifact: ModuleObjectArtifact, registry: dict[str, CompiledModule]):
    if artifact.generic_source is None:
        raise ValueError(f"module {artifact.module_id!r} has no reusable generic implementation template")
    program = Parser(Lexer(artifact.generic_source).lex()).parse()
    imports = {}
    for stmt in program.statements:
        if not isinstance(stmt, ImportDecl) or stmt.path in BUILTIN_MODULES:
            continue
        module_id = ".".join(stmt.path)
        dependency = registry.get(module_id)
        if dependency is None:
            raise ValueError(
                f"generic template {artifact.module_id!r} requires unavailable module {module_id!r}"
            )
        imports[stmt.alias or stmt.path[-1]] = dependency
    analyzer = Analyzer(artifact.module_id, imports, False)
    analyzer.analyze(program)
    return program, analyzer


def _specialize_object_generics(
    typed: IRProgram,
    artifacts: list[ModuleObjectArtifact],
    registry: dict[str, CompiledModule],
    object_functions,
    object_types,
):
    by_module = {artifact.module_id: artifact for artifact in artifacts}
    known = {fn.name for fn in object_functions}
    requested = {}
    for call in _walk_calls(typed):
        if call.name in known or "$" not in call.name:
            continue
        module_and_name = call.name.split("$", 1)[0]
        if "." not in module_and_name:
            continue
        module_id, function_name = module_and_name.rsplit(".", 1)
        artifact = by_module.get(module_id)
        if artifact is None:
            continue
        requested[call.name] = (artifact, function_name, tuple(arg.type_name for arg in call.arguments))

    if not requested:
        return []

    generated = []
    template_cache = {}
    for symbol, (artifact, function_name, argument_types) in requested.items():
        key = artifact.module_id
        if key not in template_cache:
            template_cache[key] = _template_module(artifact, registry)
        program, analyzer = template_cache[key]
        fn = analyzer.functions.get(function_name)
        if fn is None:
            raise ValueError(f"generic object template does not contain function {function_name!r}")
        concrete_types = [CoreLowerer._type_from_name(name) for name in argument_types]
        analyzer._ensure_function(fn, concrete_types, True)
        typed_template = Lowerer(analyzer, artifact.module_id).lower(program, False)

        contracts = {
            item.name: ([p.type_name for p in item.parameters], item.return_type, tuple(item.fails))
            for item in [*object_functions, *generated]
        }
        universal = ResourceUniversalLowerer(contracts, object_types).lower(typed_template)
        matches = [item for item in universal.functions if item.name == symbol]
        if len(matches) != 1:
            raise ValueError(f"generic object specialization {symbol!r} was not produced exactly once")
        generated.append(matches[0])
        known.add(symbol)
    return generated


def lower_direct_entry(path: Path, source_root: Path | None = None) -> UProgram:
    root = compile_entry(path, source_root)
    typed, interface_modules = typed_source_project(root, allow_interfaces=True)
    artifacts = [_load_object(mod) for mod in interface_modules]
    object_functions = [fn for artifact in artifacts for fn in artifact.functions]
    object_types = [item for artifact in artifacts for item in artifact.types]

    generated_generic_functions = _specialize_object_generics(
        typed,
        artifacts,
        _module_registry(root),
        object_functions,
        object_types,
    )
    object_functions.extend(generated_generic_functions)

    external_contracts = {
        fn.name: ([parameter.type_name for parameter in fn.parameters], fn.return_type, tuple(fn.fails))
        for fn in object_functions
    }
    if len(external_contracts) != len(object_functions):
        raise ValueError("duplicate function symbol across Eristavi module objects")

    # Imported object contracts and nominal layouts are injected directly into
    # Universal lowering. This supports scalar and aggregate signatures without
    # synthesizing fake source bodies or reopening dependency source.
    program = ResourceUniversalLowerer(external_contracts, object_types).lower(typed)

    source_names = {fn.name for fn in program.functions}
    duplicates = source_names.intersection(fn.name for fn in object_functions)
    if duplicates:
        raise ValueError(
            "duplicate function symbol while linking Eristavi module objects: "
            + ", ".join(sorted(duplicates))
        )
    combined_functions = list(program.functions) + object_functions
    return optimize_program(UProgram(combined_functions, program.entry, list(program.types)))
