from __future__ import annotations

from pathlib import Path

from .ir import IRProgram
from .ir_text import Lowerer
from .object_artifact import ModuleObjectArtifact
from .project import CompiledModule, compile_entry, compile_module
from .universal_ir import UProgram
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
    universal = ResourceUniversalLowerer().lower(typed)
    prefix = mod.module_id + "."
    own_functions = tuple(fn for fn in universal.functions if fn.name.startswith(prefix))
    own_types = tuple(item for item in universal.types if item.name.startswith(prefix))
    return ModuleObjectArtifact(
        mod.module_id,
        mod.interface.digest,
        mod.interface.dependencies,
        own_functions,
        own_types,
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


def lower_direct_entry(path: Path, source_root: Path | None = None) -> UProgram:
    root = compile_entry(path, source_root)
    typed, interface_modules = typed_source_project(root, allow_interfaces=True)
    artifacts = [_load_object(mod) for mod in interface_modules]
    object_functions = [fn for artifact in artifacts for fn in artifact.functions]
    object_types = [item for artifact in artifacts for item in artifact.types]

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
    return UProgram(combined_functions, program.entry, list(program.types))
