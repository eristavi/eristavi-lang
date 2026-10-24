from __future__ import annotations

from dataclasses import dataclass
from itertools import count
from typing import Union

_counter = count(1)

@dataclass(frozen=True)
class NamedType:
    name: str

@dataclass(frozen=True)
class TextViewType:
    kind: str

@dataclass(frozen=True)
class MaybeType:
    inner: TypeLike

@dataclass(frozen=True)
class IdentityType:
    inner: TypeLike

@dataclass(frozen=True)
class ListType:
    element: TypeLike

@dataclass(frozen=True)
class ResourceType:
    name: str
    cleanup_errors: tuple[str, ...] = ()

@dataclass(frozen=True)
class AnyErrorType:
    pass

@dataclass(frozen=True)
class NoValueType:
    pass

@dataclass
class TypeVar:
    label: str = "T"
    instance: TypeLike | None = None
    id: int = 0
    allowed_names: set[str] | None = None
    def __post_init__(self):
        if not self.id:
            self.id = next(_counter)

TypeLike = Union[NamedType, TextViewType, MaybeType, IdentityType, ListType, ResourceType, AnyErrorType, NoValueType, TypeVar]

INT = NamedType("Int")
FLOAT = NamedType("Float")
BOOL = NamedType("Bool")
TEXT = NamedType("Text")
NO_VALUE = NoValueType()
ANY_ERROR = AnyErrorType()
TEXT_CHARACTERS = TextViewType("characters")
TEXT_SCALARS = TextViewType("scalars")
TEXT_BYTES = TextViewType("bytes")


def resolve(t: TypeLike) -> TypeLike:
    if isinstance(t, TypeVar) and t.instance is not None:
        t.instance = resolve(t.instance)
        return t.instance
    return t


def occurs(v: TypeVar, t: TypeLike) -> bool:
    t = resolve(t)
    if t is v:
        return True
    if isinstance(t, (MaybeType, IdentityType)):
        return occurs(v, t.inner)
    if isinstance(t, ListType):
        return occurs(v, t.element)
    return False


def unify(a: TypeLike, b: TypeLike) -> TypeLike:
    a = resolve(a); b = resolve(b)
    if a is b:
        return a
    if isinstance(a, TypeVar):
        if isinstance(b, TypeVar):
            allowed = None
            if a.allowed_names is not None and b.allowed_names is not None: allowed = set(a.allowed_names) & set(b.allowed_names)
            elif a.allowed_names is not None: allowed = set(a.allowed_names)
            elif b.allowed_names is not None: allowed = set(b.allowed_names)
            if allowed is not None and not allowed: raise TypeError("generic type constraints are incompatible")
            a.allowed_names = allowed
            b.instance = a
            return a
        if occurs(a, b): raise TypeError("recursive type inference")
        if a.allowed_names is not None:
            bb=resolve(b)
            if not isinstance(bb,NamedType) or bb.name not in a.allowed_names:
                raise TypeError(f"{describe(bb)} does not satisfy inferred generic operation constraints")
        a.instance = b
        return b
    if isinstance(b, TypeVar): return unify(b, a)
    if type(a) is not type(b):
        raise TypeError(f"cannot unify {describe(a)} with {describe(b)}")
    if isinstance(a, NamedType):
        if a.name != b.name:  # type: ignore[attr-defined]
            raise TypeError(f"cannot unify {a.name} with {b.name}")
        return a
    if isinstance(a, TextViewType):
        if a.kind != b.kind:  # type: ignore[attr-defined]
            raise TypeError(f"cannot unify {describe(a)} with {describe(b)}")
        return a
    if isinstance(a, ResourceType):
        if a.name != b.name:  # type: ignore[attr-defined]
            raise TypeError(f"cannot unify {describe(a)} with {describe(b)}")
        return a
    if isinstance(a, MaybeType):
        unify(a.inner, b.inner)  # type: ignore[attr-defined]
        return a
    if isinstance(a, IdentityType):
        unify(a.inner, b.inner)  # type: ignore[attr-defined]
        return a
    if isinstance(a, ListType):
        unify(a.element, b.element)  # type: ignore[attr-defined]
        return a
    if isinstance(a, (AnyErrorType, NoValueType)):
        return a
    raise TypeError(f"cannot unify {describe(a)} with {describe(b)}")


def equivalent(a: TypeLike, b: TypeLike) -> bool:
    try:
        aa = clone_type(a)
        bb = clone_type(b)
        unify(aa, bb)
        return True
    except TypeError:
        return False


def clone_type(t: TypeLike, vars_map: dict[int, TypeVar] | None = None) -> TypeLike:
    vars_map = vars_map if vars_map is not None else {}
    t = resolve(t)
    if isinstance(t, TypeVar):
        if t.id not in vars_map:
            vars_map[t.id] = TypeVar(t.label, allowed_names=set(t.allowed_names) if t.allowed_names is not None else None)
        return vars_map[t.id]
    if isinstance(t, NamedType): return t
    if isinstance(t, TextViewType): return t
    if isinstance(t, ResourceType): return t
    if isinstance(t, MaybeType): return MaybeType(clone_type(t.inner, vars_map))
    if isinstance(t, IdentityType): return IdentityType(clone_type(t.inner, vars_map))
    if isinstance(t, ListType): return ListType(clone_type(t.element, vars_map))
    if isinstance(t, AnyErrorType): return ANY_ERROR
    if isinstance(t, NoValueType): return NO_VALUE
    raise AssertionError(t)


def has_unresolved(t: TypeLike) -> bool:
    t = resolve(t)
    if isinstance(t, TypeVar): return True
    if isinstance(t, (MaybeType, IdentityType)): return has_unresolved(t.inner)
    if isinstance(t, ListType): return has_unresolved(t.element)
    return False


def describe(t: TypeLike) -> str:
    t = resolve(t)
    if isinstance(t, NamedType): return t.name
    if isinstance(t, TextViewType): return f"Text {t.kind} view"
    if isinstance(t, ResourceType): return t.name
    if isinstance(t, MaybeType): return f"maybe {describe(t.inner)}"
    if isinstance(t, IdentityType): return f"identity {describe(t.inner)}"
    if isinstance(t, ListType):
        return f"List of {describe(t.element)}"
    if isinstance(t, TypeVar): return f"{t.label}{t.id}"
    if isinstance(t, AnyErrorType): return "checked error"
    if isinstance(t, NoValueType): return "no-value"
    return str(t)

def unresolved_ids(t: TypeLike) -> set[int]:
    t=resolve(t)
    if isinstance(t,TypeVar): return {t.id}
    if isinstance(t,(MaybeType,IdentityType)): return unresolved_ids(t.inner)
    if isinstance(t,ListType): return unresolved_ids(t.element)
    return set()
