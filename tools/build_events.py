"""Persistent, streaming diagnostics for completed-batch build qualification."""
from __future__ import annotations
import codecs
import contextlib
import json
import os
from pathlib import Path
import selectors
import shlex
import signal
import subprocess
import sys
import time


def write_json(path, value):
    path=Path(path)
    temporary=path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    temporary.replace(path)


def record_finally(action):
    """Do not replace a command failure with a secondary evidence-write failure."""
    primary_active=sys.exc_info()[0] is not None
    try:
        action()
    except OSError as error:
        if not primary_active:raise
        print(f'[build] warning: could not finish evidence: {error}',file=sys.stderr,flush=True)

def stop_group(process):
    try:
        os.killpg(process.pid,signal.SIGKILL)
    except ProcessLookupError:
        pass


class BuildJournal:
    def __init__(self, directory=None, *, timeout=900):
        self.directory=Path(directory) if directory is not None else None
        self.started=time.monotonic()
        self.timeout=timeout
        self.number=0
        self.stage_name='prepare'
        self.state={'status':'running','stage':self.stage_name,'repeatable':False,
                    'offline_audit_completed':False}
        if self.directory is not None:
            (self.directory/'commands').mkdir(parents=True,exist_ok=True)
            self.save()

    def save(self):
        if self.directory is not None:
            self.state['elapsed_seconds']=time.monotonic()-self.started
            write_json(self.directory/'qualification.json',self.state)

    def event(self, kind, **fields):
        if self.directory is not None:
            row={'elapsed_seconds':time.monotonic()-self.started,'kind':kind,**fields}
            with (self.directory/'events.jsonl').open('a',encoding='utf-8') as stream:
                stream.write(json.dumps(row,ensure_ascii=False)+'\n')
                stream.flush()

    @contextlib.contextmanager
    def stage(self, name):
        self.stage_name=name
        self.state.update(stage=name,active_compiler_phases=[])
        self.save();self.event('stage_begin',stage=name)
        print(f'[build] begin {name}',flush=True)
        start=time.monotonic()
        try:
            yield
        except BaseException:
            record_finally(lambda:self.event('stage_failed',stage=name,seconds=time.monotonic()-start))
            raise
        else:
            seconds=time.monotonic()-start
            self.state.setdefault('stage_seconds',{})[name]=seconds
            self.save();self.event('stage_end',stage=name,seconds=seconds)
            print(f'[build] end {name} ({seconds:.3f}s)',flush=True)

    def run(self, args, *, timeout=None, stdout_path=None, echo_stdout=False, check=True, **kwargs):
        """Capture byte-exact outputs, stream stderr, and kill the group on timeout.

        stdout_path is a separate tee for large generated files; in that mode the
        CompletedProcess stdout is empty. Raw command logs remain available too.
        """
        args=list(map(str,args))
        timeout=self.timeout if timeout is None else timeout
        if timeout<=0:raise ValueError('command timeout must be positive')
        self.number+=1
        prefix=self.directory/'commands'/f'{self.number:04d}' if self.directory else None
        command={'args':args,'stage':self.stage_name,'status':'running','timeout_seconds':timeout,
                 'active_compiler_phases':[]}
        if kwargs.get('cwd') is not None:command['cwd']=str(kwargs['cwd'])
        if stdout_path is not None:
            stdout_path=Path(stdout_path)
            stdout_path.parent.mkdir(parents=True,exist_ok=True)
            command['output_file']=str(stdout_path)
        start=time.monotonic();last_save=0;pending='';tail='';output=bytearray();errors=bytearray()
        decoder=codecs.getincrementaldecoder('utf-8')(errors='replace')
        stdout_decoder=codecs.getincrementaldecoder('utf-8')(errors='replace')
        def save_command(force=False):
            nonlocal last_save
            now=time.monotonic()
            if force or now-last_save>=0.5:
                command['elapsed_seconds']=now-start
                if prefix:write_json(prefix.with_suffix('.json'),command)
                self.state.update(command=self.number,command_args=args,
                                  active_compiler_phases=list(command['active_compiler_phases']))
                self.save();last_save=now
        def stderr_text(text):
            nonlocal pending,tail
            # Diagnostics are visible on success as well as failure. They never
            # share the stdout stream used for generated assembly/reports.
            sys.stderr.write(text);sys.stderr.flush()
            tail=(tail+text)[-16384:]
            pending+=text
            while '\n' in pending:
                line,pending=pending.split('\n',1)
                if line.startswith('[erist-phase] '):
                    try:
                        record=json.loads(line[len('[erist-phase] '):])
                    except ValueError:
                        continue
                    if not isinstance(record,dict) or record.get('event') not in ('begin','end'):
                        continue
                    if not isinstance(record.get('phase'),str) or not isinstance(record.get('subject'),str):
                        continue
                    record={key:record[key] for key in ('event','phase','subject')}
                    stack=command['active_compiler_phases']
                    if record['event']=='begin':stack.append(record)
                    else:
                        for index in range(len(stack)-1,-1,-1):
                            if all(stack[index][k]==record[k] for k in ('phase','subject')):
                                del stack[index:];break
                    self.event('compiler_phase',command=self.number,**record)
                    save_command()
            # Bound parsing memory for an unterminated diagnostic line; raw bytes
            # are still preserved in the command stderr log.
            pending=pending[-65536:]
        process=None;timed_out=False;drain_deadline=None
        self.event('command_begin',command=self.number,args=args,stage=self.stage_name)
        save_command(True)
        try:
            with contextlib.ExitStack() as files:
                out_log=files.enter_context(prefix.with_suffix('.stdout').open('wb')) if prefix else None
                err_log=files.enter_context(prefix.with_suffix('.stderr').open('wb')) if prefix else None
                generated=files.enter_context(stdout_path.open('wb')) if stdout_path is not None else None
                process=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                         start_new_session=True,**kwargs)
                command['pid']=process.pid
                selector=files.enter_context(selectors.DefaultSelector())
                selector.register(process.stdout,selectors.EVENT_READ,'stdout')
                selector.register(process.stderr,selectors.EVENT_READ,'stderr')
                files.callback(process.stdout.close);files.callback(process.stderr.close)
                deadline=start+timeout
                while selector.get_map():
                    remaining=deadline-time.monotonic()
                    if remaining<=0 and not timed_out:
                        timed_out=True;stop_group(process);drain_deadline=time.monotonic()+2
                    if drain_deadline is not None and time.monotonic()>drain_deadline:
                        command["output_drain_truncated"]=True
                        break
                    for key,_ in selector.select(timeout=max(0,min(0.2,remaining)) if not timed_out else 0.2):
                        data=os.read(key.fd,65536)
                        if not data:
                            selector.unregister(key.fileobj);continue
                        if key.data=='stdout':
                            if out_log:out_log.write(data);out_log.flush()
                            if echo_stdout:
                                sys.stderr.write(stdout_decoder.decode(data));sys.stderr.flush()
                            if generated:generated.write(data);generated.flush()
                            else:output.extend(data)
                        else:
                            errors.extend(data)
                            if err_log:err_log.write(data);err_log.flush()
                            stderr_text(decoder.decode(data))
                    save_command()
                stderr_text(decoder.decode(b'',final=True))
                if echo_stdout:
                    sys.stderr.write(stdout_decoder.decode(b'',final=True));sys.stderr.flush()
                # A process may close its pipes before it exits. Keep the same
                # deadline, rather than waiting indefinitely after EOF.
                try:code=process.wait(timeout=max(0,deadline-time.monotonic()))
                except subprocess.TimeoutExpired:
                    timed_out=True;stop_group(process);code=process.wait()
                command['returncode']=code
                if timed_out:
                    command['status']='timeout'
                    raise subprocess.TimeoutExpired(args,timeout,stderr=tail)
                command['status']='success' if code==0 else 'failed'
                if code and check:
                    raise RuntimeError(f'command exited {code}: {shlex.join(args)}\n{tail}')
                return subprocess.CompletedProcess(args,code,output.decode('utf-8'),errors.decode('utf-8',errors='replace'))
        except BaseException as error:
            if command['status']=='running':
                command.update(status='interrupted' if isinstance(error,KeyboardInterrupt) else 'failed',error=str(error))
            raise
        finally:
            if process is not None and process.poll() is None:
                stop_group(process);process.wait()
            def finish():
                save_command(True)
                self.event('command_end',command=self.number,status=command['status'],seconds=time.monotonic()-start)
            record_finally(finish)
