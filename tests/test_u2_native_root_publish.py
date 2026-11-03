"""Focused U2 canonical verified-root -> owned x86-64 GC publication proof."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
import platform

from compiler.erist.cli import build_native
from test_freestanding_graph_values import FINISH, descriptors
from test_freestanding_text_lifetimes import (
    FreestandingTextLifetimeTests, audit_slot_count,
)

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(
    platform.system() == "Linux"
    and platform.machine().lower() in ("x86_64", "amd64"),
    "opt-in owned machine-root test requires Linux x86-64",
)
class U2NativeRootPublishTests(unittest.TestCase):
    def test_generated_scoped_bind_publish_release_survives_forced_gc(self):
        for program in ("as", "ld", "nm", "readelf"):
            if not shutil.which(program):
                self.skipTest(program+" unavailable")
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp)
            (directory/"compiler").symlink_to(
                ROOT/"src/compiler", target_is_directory=True)
            source=(ROOT/"tests/fixtures/u2_scoped_owners.eri").read_text()
            imports="import compiler.u2_scoped_owners as owners;"
            self.assertIn(imports,source)
            source=source.replace(
                imports, imports+"\n"
                "import compiler.u2_root_map as rootMap;\n"
                "import compiler.u2_native_root_x86_64 as nativeRoot;",1)
            insertion=(
                "let mutate be try budget.constructionPhase(owner); "
                "let revision be fn.revision;"
            )
            self.assertIn(insertion,source)
            source=source.replace(
                insertion, insertion+"\n"
                "    let map be try rootMap.create(fn,graph,mutate);\n"
                "    try nativeRoot.emit(map,fn,graph,mutate,7);\n"
                "    try rootMap.close(map);",1)
            marker="continuation.InvalidBinding,owners.InvalidOwnership,ProbeError {"
            self.assertIn(marker,source)
            source=source.replace(
                marker,"continuation.InvalidBinding,owners.InvalidOwnership,"
                "rootMap.InvalidRoots,nativeRoot.Unsupported,ProbeError {",1)
            errors='else error ProbeError { output("probe:"+error.message);'
            self.assertIn(errors,source)
            source=source.replace(
                errors,
                'else error rootMap.InvalidRoots { output("roots:"+error.message); process.setExitCode(1); }\n'
                'else error nativeRoot.Unsupported { output("native:"+error.message); process.setExitCode(1); }\n'
                +errors,1)
            closing='output("u2-scoped-owners:ok");'
            self.assertIn(closing,source)
            source=source.replace(closing,"",1)
            file=directory/"root_emitter.eri"
            file.write_text(source,encoding="utf-8")
            generator=directory/"root_emitter"
            self.assertEqual(build_native(file,generator,directory),0)
            result=subprocess.run(
                [str(generator)],capture_output=True,text=True,timeout=120)
            self.assertEqual(
                (result.returncode,result.stderr),(0,""),result.stdout[-1200:])
            emission=result.stdout
            matches=re.findall(
                r"^\.globl erist_u2_publish_7_(\d+)$",emission,re.M)
            self.assertEqual(len(matches),5)
            self.assertEqual(len(set(matches)),5)
            self.assertEqual(
                len(re.findall(r"^    \.byte 5$",emission,re.M)),5)
            self.assertIn(".globl erist_u2_bind_7",emission)
            self.assertIn("    movq $0,32(%rsi)",emission)
            first=matches[0]
            native=(ROOT/"tests/fixtures/u2_root_publish_native.s").read_text()
            self.assertEqual(native.count("@INSTRUCTION@"),2)
            native=native.replace("@INSTRUCTION@",first)
            runner=directory/"graph_runtime"
            self.assertEqual(build_native(
                ROOT/"src/graph_value_runtime.eri",runner,ROOT/"src"),0)
            generated=subprocess.run(
                [str(runner)],capture_output=True,text=True,timeout=60)
            self.assertEqual((generated.returncode,generated.stderr),(0,""))
            runtime=audit_slot_count(generated.stdout)
            marker="erist_rt_text_collect:\n"
            self.assertEqual(runtime.count(marker),1)
            runtime=runtime.replace(
                marker,
                marker+"    incq erist_rt_u2_generated_gc_visits(%rip)\n",1)
            runtime+=(
                "\n.bss\n.p2align 3\n"
                ".globl erist_rt_u2_generated_gc_visits\n"
                "erist_rt_u2_generated_gc_visits:\n.quad 0\n")
            execution=FreestandingTextLifetimeTests._link_run(
                self,directory,"u2-verified-native-root",runtime,
                descriptors()+emission+native+FINISH)
            self.assertEqual(
                (execution.returncode,execution.stdout,execution.stderr),
                (0,b"u2-emitted-root\n",b""))
