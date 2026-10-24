from __future__ import annotations

from pathlib import Path

from .diagnostics import SourceLocation
from .ir import IRConst, IRFunction, IRParameter, IRProgram, IRReturn
from .ir_text import Lowerer
from .object_artifact import ModuleObjectArtifact
from .project import CompiledModule, compile_entry, compile_module
from .universal_ir import BOOL, F64, I64, TEXT, VOID, UFunction, UProgram, UniversalLowerer


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
    universal = UniversalLowerer().lower(typed)
    prefix = mod.module_id + "."
    own = tuple(fn for fn in universal.functions if fn.name.startswith(prefix))
    return ModuleObjectArtifact(
        mod.module_id,
        mod.interface.digest,
        mod.interface.dependencies,
        own,
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


def _source_type(t: str) -> str:
    mapping = {I64: "Int", F64: "Float", BOOL: "Bool", TEXT: "Text"}
    if t in mapping:
        return mapping[t]
    raise ValueError(f"module object linking does not yet synthesize signature type {t!r}")


def _signature_stub(fn: UFunction) -> IRFunction:
    location = SourceLocation(1, 1)
    params = [IRParameter(p.name, _source_type(p.type_name)) for p in fn.parameters]
    if fn.return_type == VOID:
        body = [IRReturn(None, location)]
        result = None
    else:
        source_type = _source_type(fn.return_type)
        default = {"Int": 0, "Float": 0.0, "Bool": False, "Text": ""}[source_type]
        body = [IRReturn(IRConst(source_type, location, default), location)]
        result = source_type
    return IRFunction(fn.name, params, result, body, fn.public, ())


def lower_direct_entry(path: Path, source_root: Path | None = None) -> UProgram:
    root = compile_entry(path, source_root)
    typed, interface_modules = typed_source_project(root, allow_interfaces=True)
    artifacts = [_load_object(mod) for mod in interface_modules]
    object_functions = [fn for artifact in artifacts for fn in artifact.functions]

    # Signature stubs exist only while lowering source calls.  They are removed
    # immediately and replaced by the serialized implementation functions.
    object_names = {fn.name for fn in object_functions}
    typed_with_contracts = IRProgram(
        typed.structs,
        typed.functions + [_signature_stub(fn) for fn in object_functions],
        typed.entry,
    )
    program = UniversalLowerer().lower(typed_with_contracts)
    source_functions = [
        fn for fn in program.functions
        if fn.name == program.entry or fn.name not in object_names
    ]
    combined = source_functions + object_functions
    names = [fn.name for fn in combined]
    if len(names) != len(set(names)):
        raise ValueError("duplicate function symbol while linking Eristavi module objects")
    return UProgram(combined, program.entry)
