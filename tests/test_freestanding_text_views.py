"""Hosted byte/scalar view ABI, lifetime and bounds qualification."""
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native
import test_freestanding_text_lifetimes as lifetime_tests

ROOT = Path(__file__).resolve().parents[1]
STARTUP = '''.text
.globl _start
_start:
    xorl %ebp,%ebp
    call erist_entry
    call erist_rt_text_collect
    call erist_rt_text_live_buffers
    testq %rax,%rax
    jne .Lviews_fail
    call erist_rt_allocator_release_all
    testq %rax,%rax
    jne .Lviews_fail
    xorl %edi,%edi
    jmp erist_rt_exit
.Lviews_fail:
    movl $1,%edi
    jmp erist_rt_exit
'''


@unittest.skipUnless(platform.system() == 'Linux' and platform.machine().lower() in ('x86_64', 'amd64'),
                     'freestanding Text views currently target Linux x86-64')
class FreestandingTextViewTests(unittest.TestCase):
    def test_views_escape_copy_keep_storage_and_check_bounds(self):
        for tool in ('as', 'ld', 'readelf', 'nm'):
            if not shutil.which(tool):
                self.skipTest(f'{tool} unavailable')
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td)
            generator, frontend = directory/'runtime', directory/'frontend'
            self.assertEqual(build_native(ROOT/'src/text_view_runtime.eri', generator, ROOT/'src'), 0)
            self.assertEqual(build_native(ROOT/'src/frontend.eri', frontend, ROOT/'src'), 0)
            emitted = subprocess.run([str(generator)], capture_output=True, text=True, timeout=30)
            self.assertEqual((emitted.returncode, emitted.stderr), (0, ''))

            def execute(name, source):
                path = directory/(name+'.eri')
                path.write_text(source)
                compiled = subprocess.run([str(frontend), 'emit-asm', str(path)],
                                          capture_output=True, text=True, timeout=30)
                self.assertEqual((compiled.returncode, compiled.stderr), (0, ''))
                return lifetime_tests.FreestandingTextLifetimeTests._link_run(
                    self, directory, name, emitted.stdout, compiled.stdout+STARTUP)

            program = (ROOT/'examples/freestanding_text_views.eri').read_text()
            result = execute('views', program)
            expected = b'8\n65\n204\n129\n240\n128\n0\n4\nA\n\xcc\x81\n\xf0\x9f\x98\x80\n\0\n8\n0\n0\n'
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, expected, b''))
            cases = [('bytes_negative', '"A".bytes[-1]'),
                     ('bytes_end', '"A".bytes[1]'),
                     ('bytes_empty', '"".bytes[0]'),
                     ('scalars_negative', '"😀".scalars[-1]'),
                     ('scalars_end', '"😀".scalars[1]'),
                     ('scalars_empty', '"".scalars[0]')]
            for name, expression in cases:
                with self.subTest(name=name):
                    result = execute(name, 'output('+expression+');')
                    self.assertEqual((result.returncode, result.stdout, result.stderr),
                                     (1, b'', b'Eristavi runtime fault: Text view index out of bounds\n'))
