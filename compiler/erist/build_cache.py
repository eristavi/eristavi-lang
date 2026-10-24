from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import shutil

from .interface import ModuleInterface
from .lexer import Lexer
from .object_artifact import OBJECT_IR, OBJECT_VERSION, ModuleObjectArtifact
from .parser import Parser
from .direct_project import compile_module_object, object_path
from .project import compile_module
from .syntax import ImportDecl
from .unicode_support import UNICODE_VERSION

CACHE_SCHEMA = "eristavi.build-cache"
CACHE_VERSION = 1


@dataclass(frozen=True)
class CachedModuleArtifacts:
    module_id: str
    key: str
    interface_path: Path
    object_path: Path
    cache_hit: bool


class ArtifactBuilder:
    """Content-addressed bootstrap builder for reusable Eristavi modules.

    A module cache key depends on its complete source bytes, toolchain artifact
    schema/Unicode version, and only the *public interface digest* of each
    dependency. Therefore a dependency's private implementation-only edit
    rebuilds that dependency object but does not unnecessarily invalidate an
    importer whose semantic contract is unchanged.
    """

    def __init__(self, source_root: Path, cache_root: Path | None = None):
        self.source_root = source_root.resolve()
        self.cache_root = (cache_root or (self.source_root / ".erist-cache")).resolve()
        self._done: dict[str, CachedModuleArtifacts] = {}
        self._building: set[str] = set()

    def _logical(self, path: Path) -> str:
        rel = path.resolve().relative_to(self.source_root)
        return ".".join(rel.with_suffix("").parts)

    def _imports(self, path: Path):
        source = path.read_text(encoding="utf-8")
        program = Parser(Lexer(source).lex()).parse()
        return source, [
            stmt for stmt in program.statements
            if isinstance(stmt, ImportDecl) and stmt.path != ("std", "files")
        ]

    @staticmethod
    def _digest_bytes(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _external_dependency(self, module_id: str, source_path: Path):
        interface_path = source_path.with_suffix(".eri-interface.json")
        object_file = object_path(source_path)
        if not interface_path.exists() or not object_file.exists():
            raise ValueError(
                f"dependency {module_id!r} has no source and is missing its interface/object artifacts"
            )
        interface = ModuleInterface.from_json(interface_path.read_text(encoding="utf-8"))
        artifact = ModuleObjectArtifact.from_json(object_file.read_text(encoding="utf-8"))
        if artifact.interface_digest != interface.digest:
            raise ValueError(f"dependency {module_id!r} interface/object digest mismatch")
        return interface.digest

    def build_module(self, path: Path) -> CachedModuleArtifacts:
        path = path.resolve()
        module_id = self._logical(path)
        if module_id in self._done:
            return self._done[module_id]
        if module_id in self._building:
            raise ValueError(f"circular module dependency while caching {module_id!r}")
        self._building.add(module_id)
        try:
            source, imports = self._imports(path)
            dependency_digests = []
            for stmt in imports:
                dep_id = ".".join(stmt.path)
                dep_source = self.source_root.joinpath(*stmt.path).with_suffix(".eri")
                if dep_source.exists():
                    dep = self.build_module(dep_source)
                    interface = ModuleInterface.from_json(dep.interface_path.read_text(encoding="utf-8"))
                    digest = interface.digest
                else:
                    digest = self._external_dependency(dep_id, dep_source)
                dependency_digests.append((dep_id, digest))

            fingerprint = {
                "schema": CACHE_SCHEMA,
                "version": CACHE_VERSION,
                "module": module_id,
                "unicode": UNICODE_VERSION,
                "object_version": OBJECT_VERSION,
                "object_ir": OBJECT_IR,
                "source_sha256": self._digest_bytes(source.encode("utf-8")),
                "dependencies": dependency_digests,
            }
            encoded = json.dumps(fingerprint, sort_keys=True, separators=(",", ":")).encode("utf-8")
            key = hashlib.sha256(encoded).hexdigest()
            cache_dir = self.cache_root / "objects" / key
            cached_interface = cache_dir / "module.eri-interface.json"
            cached_object = cache_dir / "module.eri-object.json"
            adjacent_interface = path.with_suffix(".eri-interface.json")
            adjacent_object = object_path(path)

            hit = cached_interface.exists() and cached_object.exists()
            if hit:
                cache_dir.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(cached_interface, adjacent_interface)
                shutil.copyfile(cached_object, adjacent_object)
            else:
                mod = compile_module(path, self.source_root)
                artifact = compile_module_object(path, self.source_root)
                cache_dir.mkdir(parents=True, exist_ok=True)
                cached_interface.write_text(mod.interface.to_json(), encoding="utf-8")
                cached_object.write_text(artifact.to_json(), encoding="utf-8")
                adjacent_interface.write_text(mod.interface.to_json(), encoding="utf-8")
                adjacent_object.write_text(artifact.to_json(), encoding="utf-8")

            manifest_dir = self.cache_root / "manifests"
            manifest_dir.mkdir(parents=True, exist_ok=True)
            (manifest_dir / (module_id.replace(".", "__") + ".json")).write_text(
                json.dumps({**fingerprint, "key": key}, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            result = CachedModuleArtifacts(module_id, key, adjacent_interface, adjacent_object, hit)
            self._done[module_id] = result
            return result
        finally:
            self._building.remove(module_id)
