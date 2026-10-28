from pathlib import Path

path = Path('tests/universal_verifier_cases.py')
s = path.read_text()
anchor = "    add('duplicate-block', 'let b be fresh(); let last be u.block(b); last.index=0; result(\"duplicate-block\",b,false);', 'cyclic/duplicate block table')\n"
case = "    add('bucket-collision', 'let b be fresh(); let last be u.block(b); last.index=257; u.jump(b,last); b.current=last; let value be u.zero(b,\"void\"); u.returnValue(b,value); result(\"bucket-collision\",b,false);')\n"
assert s.count(anchor) == 1, s.count(anchor)
assert "bucket-collision" not in s
s = s.replace(anchor, case + anchor, 1)
path.write_text(s)
