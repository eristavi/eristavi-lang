"""Exercise diagnostics with real child processes, including controlled failures."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from compiler.erist import cli

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('observable_builder',ROOT/'tools/build_offline.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
spec=importlib.util.spec_from_file_location('observable_audit',ROOT/'tools/verify_offline.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
from build_events import BuildJournal, stop_group

class BuildObservabilityTests(unittest.TestCase):
    def test_success_warnings_are_live_and_generated_stdout_is_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);ack=root/'continue';journal=BuildJournal(root/'evidence');results=[];errors=[]
            script=('import sys,json,time; from pathlib import Path; '
                    'sys.stderr.write(\'[erist-phase] {"event":"begin","phase":"lex","subject":"input λ"}\\n\');sys.stderr.flush(); '
                    f'ack=Path({str(ack)!r})\n'
                    'while not ack.exists(): time.sleep(0.01)\n'
                    'sys.stdout.buffer.write(b".text\\n.byte 42\\n");sys.stdout.flush()\n'
                    'sys.stderr.write("warning: retained on success\\n");sys.stderr.flush()\n'
                    'sys.stderr.write(\'[erist-phase] {"event":"end","phase":"lex","subject":"input λ"}\\n\')\n')
            def invoke():
                try:results.append(journal.run([sys.executable,'-c',script],timeout=8))
                except BaseException as error:errors.append(error)
            console=io.StringIO();stdout=io.StringIO()
            with contextlib.redirect_stderr(console),contextlib.redirect_stdout(stdout):
                thread=threading.Thread(target=invoke);thread.start()
                try:
                    deadline=time.monotonic()+5
                    while time.monotonic()<deadline:
                        record=root/'evidence/commands/0001.json'
                        if record.exists() and json.loads(record.read_text()).get('active_compiler_phases'):
                            break
                        time.sleep(0.01)
                    else:self.fail('phase evidence was not persisted while child was running')
                    self.assertTrue(thread.is_alive())
                    self.assertIn('"phase":"lex"',console.getvalue())
                finally:
                    ack.touch();thread.join(timeout=9)
            self.assertFalse(thread.is_alive());self.assertEqual(errors,[])
            self.assertEqual(results[0].stdout,'.text\n.byte 42\n')
            self.assertEqual(stdout.getvalue(),'')
            self.assertIn('warning: retained on success',console.getvalue())
            record=json.loads((root/'evidence/commands/0001.json').read_text())
            self.assertEqual(record['status'],'success');self.assertEqual(record['active_compiler_phases'],[])
            self.assertEqual((root/'evidence/commands/0001.stdout').read_text(),results[0].stdout)
            self.assertIn('warning: retained on success',(root/'evidence/commands/0001.stderr').read_text())

    def test_timeout_preserves_phase_partial_output_and_stops_child_group(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);heartbeat=root/'heartbeat';partial=root/'partial.s'
            child=('from pathlib import Path; import time\n'
                   f'p=Path({str(heartbeat)!r})\n'
                   'while True:\n with p.open("a") as f:f.write(".")\n time.sleep(0.02)\n')
            parent=('import sys,subprocess,time\n'
                    f'subprocess.Popen([sys.executable,"-c",{child!r}])\n'
                    'sys.stdout.write("partial assembly\\n");sys.stdout.flush()\n'
                    'sys.stderr.write(\'[erist-phase] {"event":"begin","phase":"lower-ir","subject":"compiler"}\\n\');sys.stderr.flush()\n'
                    'time.sleep(60)\n')
            def failed_build(destination,compiler,self_build,runtime,trace,journal,snapshot):
                with journal.stage('native-B-to-C-assembly'):
                    builder.run([sys.executable,'-c',parent],timeout=2,stdout_path=partial)
            original_event=BuildJournal.event
            def evidence_error(journal,kind,**fields):
                if kind in ('command_end','stage_failed') and journal.stage_name=='native-B-to-C-assembly':
                    raise OSError('simulated evidence write failure')
                return original_event(journal,kind,**fields)
            stopped=[];original_wait=subprocess.Popen.wait
            def stop_once(process):
                if stopped:raise PermissionError('process group already terminating')
                stopped.append(process.pid);stop_group(process)
            def delayed_reap(process,timeout=None):
                # macOS can expose EOF before wait(0) observes the killed child.
                if timeout is not None and timeout<=0:
                    raise subprocess.TimeoutExpired(process.args,timeout)
                return original_wait(process,timeout=timeout)
            diagnostics=io.StringIO()
            with patch('build_events.stop_group',side_effect=stop_once),patch.object(subprocess.Popen,'wait',delayed_reap),patch.object(BuildJournal,'event',evidence_error),patch.object(builder,'_build',side_effect=failed_build),patch.dict(os.environ,{'GITHUB_STEP_SUMMARY':str(root/'summary')}),contextlib.redirect_stderr(diagnostics),contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(subprocess.TimeoutExpired):builder.build(root/'bundle',runtime_profile='owned')
            record=json.loads((root/'bundle/evidence/qualification.json').read_text())
            self.assertEqual((record['status'],record['stage'],record['repeatable']),('timeout','native-B-to-C-assembly',False))
            self.assertTrue(record['source_snapshot_unchanged'])
            self.assertEqual(record['active_compiler_phases'][-1]['phase'],'lower-ir')
            self.assertEqual(partial.read_text(),'partial assembly\n')
            self.assertTrue(heartbeat.exists(),'grandchild did not start before timeout')
            size=heartbeat.stat().st_size;time.sleep(0.1);self.assertEqual(heartbeat.stat().st_size,size)
            self.assertIsNone(builder._ACTIVE_JOURNAL.get())
            self.assertEqual(len(stopped),1)
            self.assertIn('simulated evidence write failure',diagnostics.getvalue())

    def test_offline_audit_owns_timeout_cleanup_and_preserves_primary_failure(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);heartbeat=root/'heartbeat'
            child=('from pathlib import Path; import time\n'
                   f'p=Path({str(heartbeat)!r})\n'
                   'while True:\n with p.open("a") as f:f.write(".")\n time.sleep(0.02)\n')
            parent=('import subprocess,sys,time\n'
                    f'subprocess.Popen([sys.executable,"-c",{child!r}])\n'
                    'time.sleep(60)\n')
            def running_audit(bundle,journal):
                with journal.stage('execute-application'):
                    journal.run([sys.executable,'-c',parent])
            with patch.object(audit,'_verify',side_effect=running_audit),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(subprocess.TimeoutExpired):audit.verify(root/'bundle',command_timeout=2)
            record=json.loads((root/'bundle/evidence/offline-audit/qualification.json').read_text())
            self.assertEqual((record['status'],record['stage']),('timeout','execute-application'))
            self.assertTrue(heartbeat.exists(),'audit grandchild did not start before timeout')
            size=heartbeat.stat().st_size;time.sleep(0.1);self.assertEqual(heartbeat.stat().st_size,size)
            original_save=BuildJournal.save
            def failed_evidence(journal):
                if journal.state['status']=='failed':raise OSError('audit evidence unavailable')
                return original_save(journal)
            diagnostics=io.StringIO()
            with patch.object(audit,'_verify',side_effect=RuntimeError('primary audit failure')),patch.object(BuildJournal,'save',failed_evidence),contextlib.redirect_stderr(diagnostics):
                with self.assertRaisesRegex(RuntimeError,'primary audit failure'):audit.verify(root/'failed-bundle')
            self.assertIn('audit evidence unavailable',diagnostics.getvalue())

    def test_negative_audit_rejects_crash_or_unrelated_failure(self):
        with contextlib.redirect_stderr(io.StringIO()):
            result=BuildJournal().run([sys.executable,'-c','import os,signal; os.kill(os.getpid(),signal.SIGTERM)'],check=False)
        self.assertEqual(result.returncode,-signal.SIGTERM)
        with self.assertRaisesRegex(RuntimeError,'controlled rejection'):
            audit.require_expected_failure(result,1,'semantic error [')
        with self.assertRaises(RuntimeError):
            audit.require_expected_failure(subprocess.CompletedProcess([],1,'','unrelated runtime fault'),1,'semantic error [')
        audit.require_expected_failure(subprocess.CompletedProcess([],1,'','semantic error [scope]: missing'),1,'semantic error [')

    def test_successful_bootstrap_and_direct_builds_surface_both_diagnostic_streams(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source=root/'input.eri';source.write_text('output(1);')
            for build in (cli.build_native,cli.build_direct):
                for code in (0,7):
                    with self.subTest(builder=build.__name__,exit=code):
                        err=io.StringIO();out=io.StringIO()
                        completed=subprocess.CompletedProcess([],code,'stdout warning\n','stderr warning\n')
                        with patch.object(cli,'_native_direct_host',return_value=True),patch.object(cli.subprocess,'run',return_value=completed),contextlib.redirect_stderr(err),contextlib.redirect_stdout(out):
                            self.assertEqual(build(source,root/'program',root),code)
                        self.assertEqual(out.getvalue(),'')
                        self.assertEqual(err.getvalue(),'stdout warning\nstderr warning\n')

    def test_source_snapshot_detects_added_build_input(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source=root/'source';source.mkdir();(source/'src').mkdir()
            for name in ('pyproject.toml','LICENSE','DESIGN_PHILOSOPHY.md','LANGUAGE_SEMANTICS.md','FLOAT.md'):
                (source/name).write_text('input')
            def changed_build(destination,*args):
                (source/'src/added.eri').write_text('output(1);')
                (destination/'self-build.json').write_text('{"repeatable": false}')
                return destination
            with patch.object(builder,'ROOT',source),patch.object(builder,'_build',side_effect=changed_build),patch.dict(os.environ,{'GITHUB_STEP_SUMMARY':str(root/'summary')}),contextlib.redirect_stderr(io.StringIO()),contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(RuntimeError,'inputs changed'):builder.build(root/'bundle')
            record=json.loads((root/'bundle/evidence/qualification.json').read_text())
            self.assertEqual(record['status'],'failed');self.assertFalse(record['source_snapshot_unchanged'])
