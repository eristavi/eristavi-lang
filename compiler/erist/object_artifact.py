from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from .unicode_support import UNICODE_VERSION
from .universal_ir import (
    UBlock,
    UBranch,
    UField,
    UFunction,
    UInstruction,
    UJump,
    ULocal,
    UProgram,
    UReturn,
    UType,
    UValue,
)

OBJECT_SCHEMA = "eristavi.module-object"
OBJECT_VERSION = 3
OBJECT_IR = "universal-ir-v3"


def _value(v: UValue | None):
    return None if v is None else {"id": v.id, "type": v.type_name}


def _value_from(data):
    return None if data is None else UValue(int(data["id"]), str(data["type"]))


def _local(v: ULocal):
    return {"id": v.id, "name": v.name, "type": v.type_name}


def _local_from(data):
    return ULocal(int(data["id"]), str(data["name"]), str(data["type"]))


def _field(v: UField):
    return {"name": v.name, "type": v.type_name, "fixed": v.fixed}


def _field_from(data):
    return UField(str(data["name"]), str(data["type"]), bool(data.get("fixed", False)))


def _type(v: UType):
    return {
        "name": v.name,
        "error": v.is_error,
        "fields": [_field(field) for field in v.fields],
    }


def _type_from(data):
    return UType(
        str(data["name"]),
        tuple(_field_from(field) for field in data.get("fields", ())),
        bool(data.get("error", False)),
    )


def _instruction(i: UInstruction):
    return {
        "op": i.op,
        "result": _value(i.result),
        "args": [_value(v) for v in i.args],
        "local": i.local,
        "immediate": i.immediate,
    }


def _instruction_from(data):
    return UInstruction(
        str(data["op"]),
        _value_from(data.get("result")),
        tuple(_value_from(v) for v in data.get("args", ())),
        None if data.get("local") is None else int(data["local"]),
        data.get("immediate"),
    )


def _terminator(term):
    if isinstance(term, UJump):
        return {"kind": "jump", "target": term.target}
    if isinstance(term, UBranch):
        return {
            "kind": "branch",
            "condition": _value(term.condition),
            "true": term.true_target,
            "false": term.false_target,
        }
    if isinstance(term, UReturn):
        return {"kind": "return", "value": _value(term.value)}
    raise TypeError("cannot serialize missing/unknown universal terminator")


def _terminator_from(data):
    kind = data.get("kind")
    if kind == "jump":
        return UJump(str(data["target"]))
    if kind == "branch":
        return UBranch(_value_from(data["condition"]), str(data["true"]), str(data["false"]))
    if kind == "return":
        return UReturn(_value_from(data.get("value")))
    raise ValueError(f"unknown universal terminator {kind!r}")


def function_to_data(fn: UFunction) -> dict[str, Any]:
    return {
        "name": fn.name,
        "returns": fn.return_type,
        "public": fn.public,
        "fails": list(fn.fails),
        "parameters": [_local(v) for v in fn.parameters],
        "locals": [_local(v) for v in fn.locals],
        "value_count": fn.value_count,
        "blocks": [
            {
                "name": block.name,
                "instructions": [_instruction(i) for i in block.instructions],
                "terminator": _terminator(block.terminator),
            }
            for block in fn.blocks
        ],
    }


def function_from_data(data: dict[str, Any]) -> UFunction:
    return UFunction(
        str(data["name"]),
        str(data["returns"]),
        [_local_from(v) for v in data.get("parameters", ())],
        [_local_from(v) for v in data.get("locals", ())],
        [
            UBlock(
                str(block["name"]),
                [_instruction_from(i) for i in block.get("instructions", ())],
                _terminator_from(block["terminator"]),
            )
            for block in data.get("blocks", ())
        ],
        int(data.get("value_count", 0)),
        bool(data.get("public", False)),
        tuple(str(x) for x in data.get("fails", ())),
    )


@dataclass(frozen=True)
class ModuleObjectArtifact:
    module_id: str
    interface_digest: str
    dependencies: tuple[str, ...]
    functions: tuple[UFunction, ...]
    types: tuple[UType, ...] = ()
    # Bootstrap reusable-generic template. It is stored only for modules that
    # export inferred-generic functions. The source language still has no
    # generic syntax: downstream concrete specializations are requested from
    # the serialized interface contract, then compiled from this implementation
    # template after the original `.eri` file has been removed.
    generic_source: str | None = None
    unicode_version: str = UNICODE_VERSION
    schema: str = OBJECT_SCHEMA
    version: int = OBJECT_VERSION
    ir: str = OBJECT_IR

    def to_data(self) -> dict[str, Any]:
        data = {
            "schema": self.schema,
            "version": self.version,
            "ir": self.ir,
            "module": self.module_id,
            "unicode": self.unicode_version,
            "interface_digest": self.interface_digest,
            "dependencies": list(self.dependencies),
            "types": [_type(item) for item in self.types],
            "functions": [function_to_data(fn) for fn in self.functions],
        }
        if self.generic_source is not None:
            data["generic_template"] = {
                "kind": "eristavi-source-v1",
                "source": self.generic_source,
            }
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_data(), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> "ModuleObjectArtifact":
        if data.get("schema") != OBJECT_SCHEMA:
            raise ValueError("not an Eristavi module implementation artifact")
        if int(data.get("version", -1)) != OBJECT_VERSION:
            raise ValueError(f"unsupported Eristavi object version {data.get('version')!r}")
        if data.get("ir") != OBJECT_IR:
            raise ValueError(f"unsupported Eristavi object IR {data.get('ir')!r}")
        if data.get("unicode") != UNICODE_VERSION:
            raise ValueError(
                f"object requires Unicode {data.get('unicode')}, toolchain uses {UNICODE_VERSION}"
            )
        template = data.get("generic_template")
        generic_source = None
        if template is not None:
            if not isinstance(template, dict) or template.get("kind") != "eristavi-source-v1":
                raise ValueError("unsupported Eristavi generic object template")
            generic_source = str(template.get("source", ""))
        return cls(
            str(data["module"]),
            str(data["interface_digest"]),
            tuple(str(x) for x in data.get("dependencies", ())),
            tuple(function_from_data(x) for x in data.get("functions", ())),
            tuple(_type(x) if isinstance(x, UType) else _type_from(x) for x in data.get("types", ())),
            generic_source,
            str(data["unicode"]),
            str(data["schema"]),
            int(data["version"]),
            str(data["ir"]),
        )

    @classmethod
    def from_json(cls, text: str) -> "ModuleObjectArtifact":
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("Eristavi module object root must be a JSON object")
        return cls.from_data(data)

    def as_program(self) -> UProgram:
        return UProgram(list(self.functions), "__entry", list(self.types))
