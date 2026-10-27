from __future__ import annotations

from .stdlib import BUILTIN_MODULES

from dataclasses import dataclass
import hashlib
import json
from types import SimpleNamespace
from typing import Any

from .semantic import FieldInfo, StructInfo
from .typesys import (
    ANY_ERROR,
    NO_VALUE,
    AnyErrorType,
    IdentityType,
    ListType,
    MaybeType,
    NamedType,
    NoValueType,
    ResourceType,
    TextViewType,
    TypeLike,
    TypeVar,
    describe,
    resolve,
    unify,
    unresolved_ids,
)
from .unicode_support import UNICODE_VERSION

INTERFACE_SCHEMA = "eristavi.module-interface"
INTERFACE_VERSION = 1


def _type_to_data(t: TypeLike, variables: dict[int, str]) -> dict[str, Any]:
    t = resolve(t)
    if isinstance(t, TypeVar):
        name = variables.get(t.id)
        if name is None:
            name = f"T{len(variables)}"
            variables[t.id] = name
        result: dict[str, Any] = {"kind": "var", "name": name}
        if t.allowed_names is not None:
            result["allowed"] = sorted(t.allowed_names)
        return result
    if isinstance(t, NamedType):
        return {"kind": "named", "name": t.name}
    if isinstance(t, TextViewType):
        return {"kind": "text-view", "view": t.kind}
    if isinstance(t, MaybeType):
        return {"kind": "maybe", "inner": _type_to_data(t.inner, variables)}
    if isinstance(t, IdentityType):
        return {"kind": "identity", "inner": _type_to_data(t.inner, variables)}
    if isinstance(t, ListType):
        return {"kind": "list", "element": _type_to_data(t.element, variables)}
    if isinstance(t, ResourceType):
        return {"kind": "resource", "name": t.name, "cleanup_errors": list(t.cleanup_errors)}
    if isinstance(t, AnyErrorType):
        return {"kind": "any-error"}
    if isinstance(t, NoValueType):
        return {"kind": "no-value"}
    raise TypeError(f"cannot serialize interface type {t!r}")


def _type_from_data(data: dict[str, Any], variables: dict[str, TypeVar] | None = None) -> TypeLike:
    variables = variables if variables is not None else {}
    kind = data.get("kind")
    if kind == "var":
        name = str(data["name"])
        if name not in variables:
            allowed = data.get("allowed")
            variables[name] = TypeVar(name, allowed_names=set(allowed) if allowed is not None else None)
        return variables[name]
    if kind == "named":
        return NamedType(str(data["name"]))
    if kind == "text-view":
        return TextViewType(str(data["view"]))
    if kind == "maybe":
        return MaybeType(_type_from_data(data["inner"], variables))
    if kind == "identity":
        return IdentityType(_type_from_data(data["inner"], variables))
    if kind == "list":
        return ListType(_type_from_data(data["element"], variables))
    if kind == "resource":
        return ResourceType(str(data["name"]), tuple(str(x) for x in data.get("cleanup_errors", ())))
    if kind == "any-error":
        return ANY_ERROR
    if kind == "no-value":
        return NO_VALUE
    raise ValueError(f"unknown interface type kind {kind!r}")


def _unify_argument(expected: TypeLike, actual: TypeLike) -> None:
    # The decoded interface signature is already fresh. Relate its variables to
    # this caller so a generic wrapper can preserve inferred result relationships.
    ee = resolve(expected)
    aa = resolve(actual)
    if isinstance(ee, MaybeType) and not isinstance(aa, MaybeType):
        unify(ee.inner, actual)
    else:
        unify(expected, actual)


@dataclass(frozen=True)
class InterfaceField:
    name: str
    type_data: dict[str, Any]
    fixed: bool = False

    def to_data(self) -> dict[str, Any]:
        return {"name": self.name, "type": self.type_data, "fixed": self.fixed}

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> "InterfaceField":
        return cls(str(data["name"]), dict(data["type"]), bool(data.get("fixed", False)))


@dataclass(frozen=True)
class InterfaceType:
    export_name: str
    canonical_name: str
    fields: tuple[InterfaceField, ...]
    is_error: bool = False
    public: bool = False

    def to_data(self) -> dict[str, Any]:
        return {
            "name": self.export_name,
            "canonical": self.canonical_name,
            "kind": "error" if self.is_error else "type",
            "public": self.public,
            "fields": [field.to_data() for field in self.fields],
        }

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> "InterfaceType":
        return cls(
            str(data["name"]),
            str(data["canonical"]),
            tuple(InterfaceField.from_data(x) for x in data.get("fields", ())),
            data.get("kind") == "error",
            bool(data.get("public", False)),
        )


@dataclass(frozen=True)
class InterfaceParameter:
    name: str
    type_data: dict[str, Any]
    declared: bool

    def to_data(self) -> dict[str, Any]:
        return {"name": self.name, "type": self.type_data, "declared": self.declared}

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> "InterfaceParameter":
        return cls(str(data["name"]), dict(data["type"]), bool(data.get("declared", False)))


@dataclass(frozen=True)
class InterfaceFunction:
    name: str
    parameters: tuple[InterfaceParameter, ...]
    return_type: dict[str, Any]
    fails: tuple[str, ...] = ()

    def to_data(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "parameters": [parameter.to_data() for parameter in self.parameters],
            "returns": self.return_type,
            "fails": list(self.fails),
        }

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> "InterfaceFunction":
        return cls(
            str(data["name"]),
            tuple(InterfaceParameter.from_data(x) for x in data.get("parameters", ())),
            dict(data["returns"]),
            tuple(str(x) for x in data.get("fails", ())),
        )

    def instantiate(self, arguments: list[TypeLike]) -> TypeLike:
        if len(arguments) != len(self.parameters):
            raise TypeError(f"function {self.name!r} expects {len(self.parameters)} argument(s), got {len(arguments)}")
        variables: dict[str, TypeVar] = {}
        parameter_types = [_type_from_data(parameter.type_data, variables) for parameter in self.parameters]
        result_type = _type_from_data(self.return_type, variables)
        for expected, actual in zip(parameter_types, arguments):
            _unify_argument(expected, actual)
        resolved = resolve(result_type)
        argument_variables=set().union(*(unresolved_ids(arg) for arg in arguments))
        if unresolved_ids(resolved) - argument_variables:
            raise TypeError(f"interface contract for {self.name!r} leaves its result type unresolved")
        return resolved

    def declared_parameter_types(self) -> list[TypeLike | None]:
        variables: dict[str, TypeVar] = {}
        result: list[TypeLike | None] = []
        for parameter in self.parameters:
            decoded = _type_from_data(parameter.type_data, variables)
            result.append(decoded if parameter.declared else None)
        return result


@dataclass(frozen=True)
class ModuleInterface:
    module_id: str
    dependencies: tuple[str, ...]
    types: tuple[InterfaceType, ...]
    functions: tuple[InterfaceFunction, ...]
    unicode_version: str = UNICODE_VERSION
    schema: str = INTERFACE_SCHEMA
    version: int = INTERFACE_VERSION

    @classmethod
    def from_analyzer(cls, module_id: str, analyzer: Any) -> "ModuleInterface":
        reverse_names = {canonical: local for local, canonical in analyzer.local_types.items()}
        types: list[InterfaceType] = []
        for canonical, info in sorted(analyzer.structs.items()):
            if canonical not in reverse_names:
                continue
            variables: dict[int, str] = {}
            fields = tuple(
                InterfaceField(field.name, _type_to_data(field.type, variables), field.fixed)
                for field in info.fields.values()
            )
            types.append(
                InterfaceType(
                    reverse_names[canonical],
                    canonical,
                    fields,
                    info.is_error,
                    info.public,
                )
            )

        functions: list[InterfaceFunction] = []
        for name, fn in sorted(analyzer.functions.items()):
            if not fn.declaration.public:
                continue
            done = [spec for spec in fn.specializations.values() if spec.state == "done" and spec.return_type is not None]
            if not done:
                raise ValueError(f"public function {name!r} has no completed interface specialization")
            spec = done[0]
            variables: dict[int, str] = {}
            params = tuple(
                InterfaceParameter(
                    declaration.name,
                    _type_to_data(param_type, variables),
                    declared_type is not None,
                )
                for declaration, declared_type, param_type in zip(
                    fn.declaration.parameters,
                    fn.typed_parameters,
                    spec.parameter_types,
                )
            )
            result = _type_to_data(spec.return_type, variables)
            functions.append(InterfaceFunction(name, params, result, tuple(sorted(fn.fails))))

        dependencies = tuple(
            sorted(
                ".".join(path)
                for path in analyzer.imports.values()
                if path not in BUILTIN_MODULES
            )
        )
        return cls(module_id, dependencies, tuple(types), tuple(functions))

    def to_data(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "version": self.version,
            "module": self.module_id,
            "unicode": self.unicode_version,
            "dependencies": list(self.dependencies),
            "types": [item.to_data() for item in self.types],
            "functions": [item.to_data() for item in self.functions],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_data(), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> "ModuleInterface":
        if data.get("schema") != INTERFACE_SCHEMA:
            raise ValueError("not an Eristavi module interface")
        if int(data.get("version", -1)) != INTERFACE_VERSION:
            raise ValueError(f"unsupported Eristavi interface version {data.get('version')!r}")
        if data.get("unicode") != UNICODE_VERSION:
            raise ValueError(
                f"interface requires Unicode {data.get('unicode')}, toolchain uses {UNICODE_VERSION}"
            )
        return cls(
            str(data["module"]),
            tuple(str(x) for x in data.get("dependencies", ())),
            tuple(InterfaceType.from_data(x) for x in data.get("types", ())),
            tuple(InterfaceFunction.from_data(x) for x in data.get("functions", ())),
            str(data["unicode"]),
            str(data["schema"]),
            int(data["version"]),
        )

    @classmethod
    def from_json(cls, text: str) -> "ModuleInterface":
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("Eristavi interface root must be a JSON object")
        return cls.from_data(data)

    def public_type(self, name: str) -> InterfaceType | None:
        for item in self.types:
            if item.public and item.export_name == name:
                return item
        return None

    def function(self, name: str) -> InterfaceFunction | None:
        for item in self.functions:
            if item.name == name:
                return item
        return None


class _InterfaceFunctionSymbol:
    def __init__(self, contract: InterfaceFunction):
        self.contract = contract
        self.declaration = SimpleNamespace(
            name=contract.name,
            public=True,
            parameters=[
                SimpleNamespace(name=p.name, type_annotation=(object() if p.declared else None))
                for p in contract.parameters
            ],
        )
        self.typed_parameters = contract.declared_parameter_types()
        self.explicit_return = None
        self.fails = set(contract.fails)
        self.specializations: dict[tuple[str, ...], Any] = {}


class InterfaceAnalyzerProxy:
    """Analyzer-shaped read-only view backed solely by serialized metadata."""

    def __init__(self, interface: ModuleInterface):
        self.interface = interface
        self.local_types: dict[str, str] = {}
        self.structs: dict[str, StructInfo] = {}
        for item in interface.types:
            variables: dict[str, TypeVar] = {}
            fields = {
                field.name: FieldInfo(
                    field.name,
                    _type_from_data(field.type_data, variables),
                    field.fixed,
                )
                for field in item.fields
            }
            self.structs[item.canonical_name] = StructInfo(
                item.canonical_name,
                fields,
                item.is_error,
                item.public,
            )
            if item.public:
                self.local_types[item.export_name] = item.canonical_name
        self.functions = {item.name: _InterfaceFunctionSymbol(item) for item in interface.functions}

    def _ensure_function(self, fn: _InterfaceFunctionSymbol, args: list[TypeLike], value_required: bool) -> TypeLike:
        try:
            return fn.contract.instantiate(args)
        except TypeError as exc:
            raise TypeError(str(exc)) from exc
