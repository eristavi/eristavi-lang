"""Independent structural call-contract verification for isolated U1a."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native

ROOT = Path(__file__).resolve().parents[1]
TAIL = r'''
function directCalls() fails budget.LimitError,verify.InvalidIR,ProbeError {
    let root be try budget.developmentRequest(); let shared be try budget.metadataOwner(root);
    let phase be try budget.constructionPhase(shared); let data be try meta.create(shared,phase);
    let sig be try meta.signature(data,phase,[meta.i64(),meta.pred()],[meta.i64(),meta.pred()]);
    let emptySig be try meta.signature(data,phase,[meta.i64()],[]);
    let target be try meta.declaration(data,phase,sig,"module.compute",1,63,0);
    let external be try meta.declaration(data,phase,emptySig,"module.log",2,63,1);
    let source be try meta.source(data,phase,"calls",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",32);
    let location be try meta.location(data,phase,source,0,8,0,1,1);
    try meta.freeze(data); try budget.finishPhase(phase);
    let owner be try budget.functionOwner(root,false); let construct be try budget.constructionPhase(owner);
    let routine be try build.create(data,sig,owner,construct);
    let entry be try build.block(routine,[meta.i64(),meta.pred()]);
    let join be try build.block(routine,[meta.i64(),meta.pred()]);
    let a be try build.parameter(routine,entry,0); let flag be try build.parameter(routine,entry,1);
    let first be try build.call(routine,entry,target,[a,flag],location);
    let second be try build.call(routine,entry,external,[a],location);
    try build.jump(routine,entry,join,[try build.result(routine,first,0),
        try build.result(routine,first,1)],location);
    try build.returnValues(routine,join,[try build.parameter(routine,join,0),
        try build.parameter(routine,join,1)],location);
    try build.complete(routine); try budget.finishPhase(construct);
    let harness be identity Harness { root=root; shared=shared; data=data; owner=owner;
        construct=construct; routine=routine; location=location; };
    try accepted(harness,2,"call-valid");
    let edit be try budget.constructionPhase(owner);
    try change(routine.instructions,edit,7,999);
    try rejected(harness,2,1,"call-foreign-id"); try change(routine.instructions,edit,7,target.index);
    try change(routine.operands,edit,1,a.index);
    try rejected(harness,2,1,"call-type"); try change(routine.operands,edit,1,flag.index);
    try change(routine.values,edit,8,3);
    try rejected(harness,2,1,"call-result"); try change(routine.values,edit,8,2);
    let metadataEdit be try budget.constructionPhase(shared);
    // The imported declaration is record 2, so its version is at 6+5=11.
    try change(data.declarations,metadataEdit,11,0);
    try rejected(harness,1,0,"call-import-version"); try change(data.declarations,metadataEdit,11,1);
    try accepted(harness,2,"call-restored"); try close(harness);
}
function run() returns Bool fails budget.LimitError,verify.InvalidIR,ProbeError {
    try directCalls(); return true;
}
function main() {
    let done be run()
    else error budget.LimitError { output(error.category+":"+error.message); process.setExitCode(1); return; }
    else error verify.InvalidIR { output(error.message); process.setExitCode(1); return; }
    else error ProbeError { output(error.message); process.setExitCode(1); return; };
}
main();
'''
EXPECTED = ''.join(name + ':ok\n' for name in (
    "call-valid", "call-foreign-id", "call-type", "call-result",
    "call-import-version", "call-restored",
))


class U1CallContracts(unittest.TestCase):
    def test_direct_call_declarations_and_verifier(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "compiler").symlink_to(ROOT / "src/compiler", target_is_directory=True)
            full = (ROOT / "tests/fixtures/u1_verifier.eri").read_text()
            prefix = full.split("function straight() returns", 1)[0]
            source = root / "calls.eri"
            source.write_text(prefix + TAIL)
            binary = root / "calls"
            self.assertEqual(build_native(source, binary, root), 0)
            result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=120)
            self.assertEqual((result.returncode, result.stdout, result.stderr),
                             (0, EXPECTED, ""))


if __name__ == "__main__":
    unittest.main()
