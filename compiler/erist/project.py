from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .diagnostics import SemanticError
from .lexer import Lexer
from .parser import Parser
from .semantic import Analyzer
from .syntax import ImportDecl

@dataclass
class CompiledModule:
    path: tuple[str,...]
    module_id: str
    file_path: Path
    program: object
    analyzer: Analyzer
    imports: dict[str,"CompiledModule"]

class ProjectCompiler:
    def __init__(self,source_root:Path):
        self.root=source_root.resolve(); self.cache={}; self.loading=[]
    def compile_entry(self,entry:Path)->CompiledModule:
        entry=entry.resolve()
        try: rel=entry.relative_to(self.root)
        except ValueError: raise SemanticError("entry file must be inside the configured source root")
        logical=tuple(rel.with_suffix("").parts)
        return self._load(logical,entry,True)
    def _load(self,logical,file_path,is_entry):
        if logical in self.cache:
            mod=self.cache[logical]
            if is_entry and not mod.analyzer.is_entry:
                # Recompile as entry if ever needed; uncommon.
                pass
            return mod
        if logical in self.loading:
            cycle=" -> ".join(".".join(x) for x in self.loading+[logical])
            raise SemanticError(f"circular module dependency: {cycle}")
        self.loading.append(logical)
        try:
            source=file_path.read_text(encoding="utf-8")
            program=Parser(Lexer(source).lex()).parse()
            imports={}
            for stmt in program.statements:
                if not isinstance(stmt,ImportDecl): continue
                if stmt.path==("std","files"): continue
                target=self.root.joinpath(*stmt.path).with_suffix(".eri")
                if not target.exists(): raise SemanticError(f"cannot resolve imported module {'.'.join(stmt.path)!r}",stmt.location)
                alias=stmt.alias or stmt.path[-1]
                imports[alias]=self._load(stmt.path,target,False)
            module_id=".".join(logical)
            analyzer=Analyzer(module_id,imports,is_entry)
            analyzer.analyze(program)
            mod=CompiledModule(logical,module_id,file_path,program,analyzer,imports)
            self.cache[logical]=mod
            return mod
        finally:
            self.loading.pop()

def compile_entry(path:Path,source_root:Path|None=None)->CompiledModule:
    path=path.resolve(); root=(source_root or path.parent).resolve()
    return ProjectCompiler(root).compile_entry(path)
