"""Independent physical-owner observation of U1b aggregate type/value stores.

Uses the existing acceptance-only allocator diagnostic runtime to distinguish
ACTUAL retained allocator capacity/GC reclamation from requested structural
backing, owner ledger and whole-process RSS. No production runtime change.
"""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native
from u1_native_tools import shared_u1_compilers
from test_u1_owner_physical import _decode_owner_records, _instrument_owned_runtime

ROOT=Path(__file__).resolve().parents[1]
TAGS={"metadata": "metadata", "function": "function"}


def inspect(stdout):
    entries={}
    ledger={}
    closed=False
    for line in stdout.splitlines():
        if line.startswith("u1b-physical:"):
            _,name,*parts=line.split(":")
            if len(parts)!=4:
                raise AssertionError("Invalid aggregate physical schema")
            entries[name]=tuple(map(int,parts))
        elif line.startswith("u1b-ledger:"):
            _,name,peak,traffic=line.split(":")
            ledger[name]=(int(peak),int(traffic))
        elif line=="u1b-physical-owner-cleanup:ok":
            closed=True
    if set(entries)!=set(TAGS) or set(ledger)!=set(TAGS) or not closed:
        raise AssertionError("Missing aggregate physical/owner evidence")
    for name,values in entries.items():
        objects,payload,headers,total=values
        if not (objects>0 and payload>0 and headers==objects*32 and
                total==payload+headers):
            raise AssertionError(f"Invalid {name} structural backing")
        peak,traffic=ledger[name]
        if not (peak>0 and traffic>=peak):
            raise AssertionError(f"Invalid {name} owner ledger")
    return entries,ledger


class U1BAggregatePhysicalTests(unittest.TestCase):
    def test_actual_aggregate_owner_backing_and_gc_reclamation(self):
        for exe in ("as","ld"):
            if shutil.which(exe) is None:
                self.skipTest(f"{exe} unavailable")
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/"compiler").symlink_to(ROOT/"src/compiler",target_is_directory=True)
            source=root/"physical.eri"
            source.write_text((ROOT/"tests/fixtures/u1b_aggregate_physical.eri").read_text(encoding="utf-8"),encoding="utf-8")
            executable=root/"physical-bootstrap"
            self.assertEqual(build_native(source,executable,root),0)
            c=subprocess.run([str(executable)],capture_output=True,text=True,timeout=90,check=False)
            self.assertEqual((c.returncode,c.stderr),(0,""))
            requested,ledgers=inspect(c.stdout)
            frontend,generator=shared_u1_compilers()
            emitted=subprocess.run([str(frontend),"emit-asm",str(source),
                         "--source-root",str(root),"--target","x86_64-linux"],
                         capture_output=True,text=True,timeout=180,check=False)
            self.assertEqual((emitted.returncode,emitted.stderr),(0,""))
            generated=subprocess.run([str(generator)],capture_output=True,text=True,
                         timeout=90,check=False)
            self.assertEqual((generated.returncode,generated.stderr),(0,""))
            app_asm=root/"app.s"
            app_asm.write_text(emitted.stdout,encoding="utf-8")
            app_obj=root/"app.o"
            subprocess.run(["as","--64",str(app_asm),"-o",str(app_obj)],
                           check=True,capture_output=True,timeout=30)

            def link(name,runtime_source):
                rt_asm=root/f"{name}.s"
                rt_asm.write_text(runtime_source,encoding="utf-8")
                rt_obj=root/f"{name}.o"
                subprocess.run(["as","--64",str(rt_asm),"-o",str(rt_obj)],
                               check=True,capture_output=True,timeout=30)
                target=root/name
                subprocess.run(["ld","-nostdlib","-static","-e","_start",
                                str(app_obj),str(rt_obj),"-o",str(target)],
                               check=True,capture_output=True,timeout=30)
                return target

            owned=link("u1b-owned",generated.stdout)
            result=subprocess.run([str(owned)],capture_output=True,text=True,timeout=90,check=False)
            self.assertEqual((result.returncode,result.stderr,result.stdout),
                             (0,"",c.stdout))
            with (root/"actual.bin").open("wb") as actual:
                diagnostic=link("u1b-observed",
                    _instrument_owned_runtime(generated.stdout,actual.fileno(),
                                              force_identity_collisions=True))
                test=subprocess.run([str(diagnostic)],pass_fds=(actual.fileno(),),
                                    capture_output=True,text=True,timeout=90,check=False)
            self.assertEqual((test.returncode,test.stderr,test.stdout),
                             (0,"",c.stdout))
            before,after=_decode_owner_records((root/"actual.bin").read_bytes())
            self.assertEqual((before["error"],after["error"]),(0,0))
            for name in TAGS:
                key=TAGS[name]
                objects,_,_,structural_bytes=requested[name]
                old=before["backing"][key]
                final=after["backing"][key]
                self.assertEqual(old["objects"],objects*2,name)
                self.assertGreaterEqual(old["observed_bytes"],
                                        structural_bytes+objects*128,name)
                self.assertEqual(final["live"],0,name)
                self.assertEqual(final["reclaimed_bytes"],old["observed_bytes"],name)
                self.assertEqual(final["reclaimed_objects"],old["objects"],name)
                own=before["owners"][key]
                self.assertLessEqual(own["peak"],own["traffic"],name)
                self.assertEqual(after["owners"][key]["live"],0,name)
            print("U1B_OWNER_PHYSICAL="+json.dumps({
                 "structural_backing":requested,
                 "owner_request_peak_traffic":ledgers,
                 "actual_before_gc":{k:before["backing"][v] for k,v in TAGS.items()},
                 "actual_after_gc":{k:after["backing"][v] for k,v in TAGS.items()},
                 "measurement_scope":"U1b immutable type graph and reference value-engine only; no canonical whole compiler RSS"
            },sort_keys=True),flush=True)


if __name__=="__main__":
    unittest.main()
