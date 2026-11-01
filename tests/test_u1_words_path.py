"""Independent radix-digit, current-path corruption and exact refusal contracts."""
from pathlib import Path
import platform
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native
from u1_native_tools import shared_u1_compilers

ROOT = Path(__file__).resolve().parents[1]
INDICES = (0, 15, 16, 255, 256, 4095, 4096, 65535, 65536,
           1048575, 1048576, 16777215, 16777216, 33554431)
SOURCE = '''
import compiler.u1_budget as budget;
import compiler.u1_words as words;
import std.process;
error ProbeError { message Text; }
function check(test Bool,message Text) fails ProbeError { if not test { fail ProbeError { message=message; }; } }
function category(store identity words.Words,phase identity budget.Phase,index Int) returns Text {
    let value be words.get(store,phase,index) else error budget.LimitError { return error.category; };
    return "success";
}
function exercise() fails budget.LimitError,ProbeError {
    let root be try budget.developmentRequest(); let owner be try budget.functionOwner(root,true);
    let phase be try budget.constructionPhase(owner); let store be try words.create(owner,33554432);
    // Private sparse shape fixture: materialize every radix digit boundary
    // without constructing millions of irrelevant pages. Missing paths remain
    // deliberately malformed and must still be rejected by get().
    SPARSE_INSERTS
    SPARSE_READS
    let preservedTraffic be root.traffic; let preservedLive be root.live;
    let originalRoot be store.root; store.root=none; let before be phase.used;
    try check(category(store,phase,0) == "invalid-state" and phase.used == before+1,"missing root/work order");
    store.root=originalRoot;
    let cursor be store.root; let depth be 0;
    while depth < 6 {
        if cursor != none {
            let selected identity words.Node be cursor;
            let saved be selected.c0; selected.c0=none; before=phase.used;
            try check(category(store,phase,0) == "invalid-state" and phase.used == before+depth+2,"fresh missing child/work order");
            selected.c0=saved; cursor=saved;
        } else { try check(false,"missing fixture path"); }
        depth=depth+1;
    }
    if cursor != none {
        let leaf identity words.Node be cursor;
        let oldPage be leaf.page; leaf.page=none; before=phase.used;
        try check(category(store,phase,0) == "invalid-state" and phase.used == before+7,"fresh missing page/work order");
        leaf.page=oldPage;
        if oldPage != none {
            oldPage.w0=12345;
            try check((try words.get(store,phase,0)) == 12345,"current page mutation hidden");
        }
    }
    try check(category(store,phase,-1) == "invalid-state" and category(store,phase,33554432) == "invalid-state","range checks");
    try check(root.traffic == preservedTraffic and root.live == preservedLive,"reads allocate owner storage");
    try words.freeze(store); before=phase.used;
    try check((try words.get(store,phase,0)) == 12345 and phase.used == before+7,"frozen read charge");
    try words.close(store);
    try check(category(store,phase,0) == "invalid-state","closed store read");
    try budget.finishPhase(phase); try budget.close(owner);
    try check(root.live == 0 and root.pending == 0,"backing cleanup"); try budget.close(root);
    let limit be 0;
    while limit < 7 {
        let request be try budget.developmentRequest(); let child be try budget.functionOwner(request,true);
        let construction be try budget.constructionPhase(child); let data be try words.create(child,1);
        let ignored be try words.push(data,construction,7); try budget.finishPhase(construction);
        let readPhase be try budget.phase(child,limit); let workBefore be request.work; let trafficBefore be request.traffic;
        try check(category(data,readPhase,0) == "resource-limit","read allowance must refuse");
        try check(readPhase.used == limit and request.work == workBefore+limit and request.traffic == trafficBefore,"exact refused work/traffic");
        try words.close(data); try budget.finishPhase(readPhase); try budget.close(child);
        try check(request.live == 0 and request.pending == 0,"refusal cleanup"); try budget.close(request);
        limit=limit+1;
    }
    output("words-path:ok");
}
function main() {
    exercise() else error budget.LimitError { output(error.category+":"+error.message); process.setExitCode(1); }
    else error ProbeError { output(error.message); process.setExitCode(1); };
}
main();
'''.replace('SPARSE_INSERTS', '\n'.join(
    f'store.length={index}; let inserted{i} be try words.push(store,phase,{index}+7);'
    for i, index in enumerate(INDICES))).replace('SPARSE_READS', '\n'.join(
    f'try check((try words.get(store,phase,{index})) == {index}+7,"radix index {index}");'
    f'try words.set(store,phase,{index},{index}+9);'
    f'try check((try words.get(store,phase,{index})) == {index}+9,"updated radix index {index}");'
    for index in INDICES))


class U1WordPathTests(unittest.TestCase):
    def test_current_radix_paths_and_exact_failure_charges_on_both_runtimes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "compiler").symlink_to(ROOT / "src/compiler", target_is_directory=True)
            source = root / "probe.eri"
            source.write_text(SOURCE)
            c_binary = root / "bootstrap"
            self.assertEqual(build_native(source, c_binary, root), 0)
            c = subprocess.run([str(c_binary)], capture_output=True, text=True, timeout=120)
            self.assertEqual((c.returncode, c.stdout, c.stderr), (0, "words-path:ok\n", ""))
            if platform.system() != "Linux" or platform.machine().lower() not in ("x86_64", "amd64"):
                return  # C contract executed; this backend is Linux x86-64 only.
            frontend, generator = shared_u1_compilers()
            emitted = subprocess.run([str(frontend), "emit-asm", str(source), "--source-root", str(root)],
                                     capture_output=True, text=True, timeout=120)
            runtime = subprocess.run([str(generator)], capture_output=True, text=True, timeout=120)
            for result in (emitted, runtime):
                self.assertEqual((result.returncode, result.stderr), (0, ""))
            for name, code in (("app", emitted.stdout), ("runtime", runtime.stdout)):
                (root / (name + ".s")).write_text(code)
                subprocess.run(["as", "--64", str(root / (name + ".s")), "-o", str(root / (name + ".o"))],
                               check=True, capture_output=True, timeout=60)
            owned = root / "owned"
            subprocess.run(["ld", "-nostdlib", "-static", "-e", "_start", str(root / "app.o"),
                            str(root / "runtime.o"), "-o", str(owned)], check=True, capture_output=True, timeout=60)
            run = subprocess.run([str(owned)], capture_output=True, text=True, timeout=120)
            self.assertEqual((run.returncode, run.stdout, run.stderr), (0, c.stdout, ""))
