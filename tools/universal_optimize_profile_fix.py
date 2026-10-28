from pathlib import Path

path = Path("src/compiler/universal_optimize.eri")
s = path.read_text()
old = "function routine(routine identity u.Function) {\n    let cursor be routine.blocks; while cursor != none { let current be cursor; current.live=false; cursor=current.next; }\n    let first be u.blockAt(routine,0); if first != none { visit(routine,first,profile); }"
new = "function routine(routine identity u.Function,profile identity OptProfile) {\n    profile.routines=profile.routines+1; let cursor be routine.blocks; while cursor != none { profile.totalBlocks=profile.totalBlocks+1; let current be cursor; current.live=false; cursor=current.next; }\n    let first be blockAt(routine,0,profile); if first != none { visit(routine,first,profile); }"
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new, 1)
assert "function routine(routine identity u.Function,profile identity OptProfile)" in s
path.write_text(s)
