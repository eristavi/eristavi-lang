#!/usr/bin/env python3
"""Opt-in actual verifier scratch accounting; disposable ASM only, Linux x86-64.

No production source edits, full owned self-build, new GC cadence or raised cap.
The observer owns a bounded, non-root static map; its overhead is reported apart.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from compiler.erist.cli import build_native
from u1_native_tools import shared_u1_compilers
from universal_verifier_cases import benchmark_program

CATEGORIES=['total','mask_list','word_body','word_identity','mask_access',
            'register_classes','flow_body','flow_wrapper','shared_tables',
            'verification_other','shared_runtime']
KINDS=['other_allocator_blocks','graph_backing','boxed_value_slots']
STAT_FIELDS=['allocations','traffic','live','peak','frees','freed','failures','reserved']
RECORD_WORDS=16+22+64*8
RECORD_SIZE=RECORD_WORDS*8
CALLER=('rax','rcx','rdx','rsi','rdi','r8','r9','r10','r11')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def exact(s,a,b):
    if s.count(a)!=1:raise AssertionError('unstable observer anchor: '+a[:100])
    return s.replace(a,b,1)

def hook(body,aligned=True):
    ops=['pushfq']+['pushq %'+r for r in CALLER]
    if not aligned:ops+=['subq $8,%rsp']
    ops+=body.splitlines()
    if not aligned:ops+=['leaq 8(%rsp),%rsp']
    ops+=['popq %'+r for r in reversed(CALLER)]+['popfq']
    return '\n'.join(ops)+'\n'

def symbols(trace):
    result={}
    for line in trace.splitlines():
        if not line.startswith('[erist-phase] '):continue
        e=json.loads(line[14:])
        if e.get('event')=='begin' and e.get('phase')=='universal-lower-function':
            symbol,_,name=e['subject'].partition(' ');name=name.split('$')[0]
            if name.startswith('compiler.universal_verify.'):
                if name in result:raise AssertionError('ambiguous source specialization')
                result[name]=symbol
    return result

def descriptors(app):
    start=app.index('ev_types:\n')+len('ev_types:\n')
    rows=[]
    pattern=r'\.long (-?\d+),(-?\d+)\n\.quad \.Ltype_name_(\d+)\n\.quad (\d+)\n\.quad ([^\n]+)\n'
    for m in re.finditer(pattern,app[start:]):
        k,inner,index,fields=map(int,m.groups()[:4])
        if index!=len(rows):raise AssertionError('noncontiguous type descriptors')
        name=re.search(r'(?m)^\.Ltype_name_'+str(index)+r':\n\.byte ([\d,]+)',app)
        if not name:raise AssertionError('missing descriptor name')
        text=bytes(map(int,name.group(1).split(','))).rstrip(b'\0').decode()
        rows.append((k,inner,fields,text))
    def one(predicate):
        hits=[i for i,row in enumerate(rows) if predicate(row)]
        if len(hits)!=1:raise AssertionError('ambiguous semantic descriptor '+str(hits))
        return hits[0]
    word=one(lambda r:r[3]=='compiler.universal_verify.Word' and r[2]==1)
    flow=one(lambda r:r[3]=='compiler.universal_verify.Flow' and r[2]==7)
    func=one(lambda r:r[3]=='compiler.universal_model.Function' and r[2]==6)
    wid=one(lambda r:r[0]==9 and r[1]==word)
    fid=one(lambda r:r[0]==9 and r[1]==flow)
    return {'WORD_TYPE':word,'WORD_ID_TYPE':wid,'FLOW_TYPE':flow,'FLOW_ID_TYPE':fid,
            'FLOW_MAYBE_TYPE':one(lambda r:r[0]==8 and r[1]==fid),
            'MASK_LIST_TYPE':one(lambda r:r[0]==7 and r[1]==wid),
            'INT_LIST_TYPE':one(lambda r:r[0]==7 and r[1]==1),
            'FUNCTION_TYPE':func,'TYPE_MAX':len(rows)-1}

def check_source_schema():
    for path,typename,names in [
        ('universal_verify.eri','Flow',['block','reachable','incoming','outgoing','first','second','next']),
        ('universal_verify.eri','Word',['value']),
        ('universal_model.eri','Function',['index','parameters','registers','registerTail','blocks','next'])]:
        source=(ROOT/'src/compiler'/path).read_text()
        match=re.search(r'type '+typename+r'\s*\{([^}]+)\}',source)
        actual=[part.strip().split()[0] for part in match.group(1).split(';') if part.strip()] if match else []
        if actual!=names:raise AssertionError('owning record schema changed: '+typename)

def source_scope(app,symbol,begin):
    a=app.index('\n'+symbol+':\n');b=app.index('\n.size '+symbol+',',a)
    body=app[a:b];frame=re.search(r'(?m)^subq \$(\d+), %rsp$',body)
    if not frame:raise AssertionError('unexpected source frame')
    size=int(frame.group(1))
    save='\n'.join(f'movq st_{n}(%rip),%r11\nmovq %r11,-{size+8*(i+1)}(%rbp)'
                   for i,n in enumerate(('sid','category','kind','active')))
    entry='subq $'+str(size+32)+', %rsp\n'+hook(save+'\n'+begin)
    body=body[:frame.start()]+entry+body[frame.end():]
    restore='\n'.join(f'movq -{size+8*(i+1)}(%rbp),%r11\nmovq %r11,st_{n}(%rip)'
                      for i,n in enumerate(('sid','category','kind','active')))
    body=body.replace('\nleave\nret','\n'+hook(restore)+'leave\nret')
    if symbol==symbols_global['compiler.universal_verify.routine']:
        # Pinned current source-local ABI, independently checked by type/shape and
        # exact R/B/W/N formula on every snapshot. Stop rather than guess on drift.
        if size!=4192 or body.count('call evn_scope_leave@PLT')!=1:
            raise AssertionError('routine local-layout schema changed')
        words=symbols_global['compiler.universal_verify.words']
        body=exact(body,'call '+words+'@PLT\n','call '+words+'@PLT\n'+hook(
            'movq -80(%rbp),%rdi\nmovq %rax,%rsi\nmovq -104(%rbp),%rdx\n'
            'movq $1,%rcx\ncall st_snapshot'))
        body=exact(body,'call evn_scope_leave@PLT\n',hook(
            'movq -80(%rbp),%rdi\nmovq -136(%rbp),%rsi\nmovq -104(%rbp),%rdx\n'
            'movq $2,%rcx\ncall st_snapshot')+'call evn_scope_leave@PLT\n')
    if symbol==symbols_global['compiler.universal_verify.verify']:
        body=body.replace('\nleave\nret','\nleave\nret') # scope restoration already above
        # Successful verifier output only; checked-unwind attribution is excluded.
        body=body.replace('call evn_scope_leave@PLT\n',hook('call st_end_verify')+'call evn_scope_leave@PLT\n')
    return app[:a]+body+app[b:]

def runtime_scope(runtime,label,select):
    real='.Lst_real_'+label.replace('.','_')
    active='.Lst_wrap_'+label.replace('.','_')
    prefix=f'''{label}:
pushfq
cmpq $0,st_active(%rip)
jne {active}
popfq
jmp {real}
{active}:
popfq
pushq st_sid(%rip)
pushq st_category(%rip)
pushq st_kind(%rip)
'''+hook(select)+f'''call {real}
pushfq
pushq %rax
movq 16(%rsp),%rax
movq %rax,st_kind(%rip)
movq 24(%rsp),%rax
movq %rax,st_category(%rip)
movq 32(%rsp),%rax
movq %rax,st_sid(%rip)
popq %rax
popfq
leaq 24(%rsp),%rsp
ret
{real}:
'''
    return exact(runtime,label+':\n',prefix)

def instrument(app,trace,runtime):
    global symbols_global
    symbols_global=symbols(trace)
    for name,action in [('verify','call st_begin_verify'),
                        ('routine','movq %rsi,%rdi\ncall st_begin_routine')]:
        app=source_scope(app,symbols_global['compiler.universal_verify.'+name],action)
    for name in ('words','fill','defined','define','copy','intersect'):
        app=source_scope(app,symbols_global['compiler.universal_verify.'+name],
                         'movq $4,st_category(%rip)')
    for label,selector in [('evn_object','call st_select_type'),('evn_wrap','call st_select_type'),
                           ('evn_add','call st_select_value'),
                           ('erist_rt_graph_detach','call st_select_value'),
                           ('erist_rt_graph_new_capacity','call st_select_graph'),
                           ('erist_rt_value_new','call st_select_slot'),
                           ('erist_rt_graph_prepare_index','call st_select_shared'),
                           ('.Lg_table_grow','call st_select_shared'),
                           ('.Lslots_scratch_acquire','call st_select_shared')]:
        runtime=runtime_scope(runtime,label,selector)
    runtime=exact(runtime,'.Lalloc_done:\n','.Lalloc_done:\n'+hook('movq %rax,%rdi\ncall st_allocated'))
    runtime=exact(runtime,'    testq %rdi,%rdi\n    je .Lfree_success\n',
                  '    testq %rdi,%rdi\n    je .Lst_free_null\n')
    runtime=exact(runtime,'.Lfree_success:\n','.Lfree_success:\n'+hook('movq %r12,%rdi\ncall st_freed'))
    runtime+='\n.text\n.Lst_free_null:\nxorl %eax,%eax\njmp .Lfree_done\n'
    runtime=exact(runtime,'    call erist_entry\n    movq .Lprocess_exit_code',
                  '    call erist_entry\n'+hook('movq $4,%rdi\ncall st_dump_all')+
                  '    call erist_rt_text_collect\n'+hook('movq $5,%rdi\ncall st_dump_all')+
                  '    call erist_rt_text_collect\n'+hook('movq $6,%rdi\ncall st_dump_all')+
                  '    movq .Lprocess_exit_code')
    return app,runtime

def records(path):
    data=path.read_bytes()
    if len(data)%RECORD_SIZE:raise AssertionError('truncated diagnostic record')
    result=[]
    for off in range(0,len(data),RECORD_SIZE):
        v=struct.unpack_from('<'+'Q'*RECORD_WORDS,data,off)
        if v[0]!=0x53544f5241474531 or v[11]:raise AssertionError('observer integrity failure: '+str(dict(zip(('magic','event','id','pass','kind','function','r','b','w','n','sequence','error_line'),v[:12]))))
        row=dict(zip(('magic','event','id','pass','kind','function','registers','blocks','words_per_mask',
                      'mask_words','sequence','errors','total_live','total_peak','map_live','max_probe'),v[:16]))
        if row['function']>=1<<63:row['function']-=1<<64
        row['semantic']={CATEGORIES[i]:{'bytes':v[16+2*i],'objects':v[17+2*i]} for i in range(1,11)}
        row['allocations']={}
        for cat in range(1,11):
            row['allocations'][CATEGORIES[cat]]={}
            for kind in range(3):
                start=38+(cat*3+kind)*8
                s=dict(zip(STAT_FIELDS,v[start:start+8]))
                if s['traffic']!=s['live']+s['freed'] or s['live']>s['peak'] or s['peak']>s['traffic']:
                    raise AssertionError('non-reconciling actual allocation ledger')
                row['allocations'][CATEGORIES[cat]][KINDS[kind]]=s
        row['aggregate']=dict(zip(STAT_FIELDS,v[38:46]))
        aggregate=row['aggregate']
        if aggregate['traffic']!=aggregate['live']+aggregate['freed'] or not 0<=aggregate['live']<=aggregate['peak']<=aggregate['traffic']:
            raise AssertionError('non-reconciling aggregate ledger')
        if row['id']:
            for field in ('allocations','traffic','live','frees','freed'):
                if aggregate[field]!=sum(s[field] for group in row['allocations'].values() for s in group.values()):
                    raise AssertionError('allocation categories do not reconcile to invocation')
        result.append(row)
    return result

def run(command,out,err,cap,fd=None):
    start=time.monotonic()
    with out.open('wb') as stdout,err.open('wb') as stderr:
        try:
            p=subprocess.run(list(map(str,command)),stdout=stdout,stderr=stderr,
                             timeout=cap,pass_fds=() if fd is None else (fd,))
            return {'status':'completed' if p.returncode==0 else 'failed','returncode':p.returncode,
                    'wall_seconds_observed':time.monotonic()-start}
        except subprocess.TimeoutExpired:
            return {'status':'censored','cap_seconds':cap,'wall_seconds_lower_bound':time.monotonic()-start}

def link(work,app,runtime,name,observer=None):
    objects=[]
    for suffix,text in [('app',app),('runtime',runtime)]:
        source=work/(name+'.'+suffix+'.s');source.write_text(text)
        obj=source.with_suffix('.o');subprocess.run(['as','--64',source,'-o',obj],check=True,capture_output=True)
        objects.append(obj)
    if observer:objects.append(observer)
    exe=work/name
    subprocess.run(['ld','-nostdlib','-static','-e','_start',*objects,'-o',exe],check=True,capture_output=True)
    return exe

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--cached-tools',type=Path,help='Pinned existing baseline_b.s, trace, runtime.s and baseline_c; source hash verification required')
    ap.add_argument('--large',action='store_true')
    ap.add_argument('--large-observer-only',action='store_true',help='Avoid repeating the already-censored plain large compilation')
    ap.add_argument('--fixtures',action='store_true',help='Six independently specified R/B/N shapes and two observer negative controls')
    ap.add_argument('--cap',type=int,default=90)
    a=ap.parse_args()
    if platform.system()!='Linux' or platform.machine().lower() not in ('x86_64','amd64'):raise RuntimeError('Linux x86-64 only')
    if a.cap<5 or a.cap>90:raise ValueError('cap must remain 5..90 seconds')
    check_source_schema()
    output=a.output.resolve();output.mkdir(parents=True,exist_ok=True)
    initial={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'src').rglob('*.eri'))}
    with tempfile.TemporaryDirectory(prefix='verifier-storage-') as td:
        work=Path(td)
        if a.cached_tools:
            cache=a.cached_tools.resolve();saved=json.loads((cache/'build-inputs.json').read_text())['manifest']
            if saved!={k.removeprefix('src/'):v for k,v in initial.items()}:raise AssertionError('cached source mismatch')
            frontend=cache/'baseline_c';app=(cache/'baseline_b.s').read_text();trace=(cache/'baseline_b.s.stderr').read_text();runtime=(cache/'runtime.s').read_text()
        else:
            frontend,generator=shared_u1_compilers()
            runtime=subprocess.check_output([generator],text=True,timeout=90)
            emitted=subprocess.run([frontend,'emit-asm',ROOT/'src/frontend.eri','--source-root',ROOT/'src','--trace-phases'],capture_output=True,text=True,timeout=90)
            if emitted.returncode:raise AssertionError(emitted.stderr[-1000:])
            app,trace=emitted.stdout,emitted.stderr
        types=descriptors(app)
        prof_app,prof_runtime=instrument(app,trace,runtime)
        plain=link(work,app,runtime,'plain')
        with (output/'records.bin').open('wb') as stream:
            defines=[f'-D{k}={v}' for k,v in types.items()]+[f'-DOUTPUT_FD={stream.fileno()}']
            observer=work/'observer.o'
            subprocess.run([os.environ.get('CC','gcc'),'-std=c11','-O2','-ffreestanding','-fno-builtin',
                            '-fno-stack-protector','-fno-pie','-mgeneral-regs-only',*defines,'-c',
                            ROOT/'tools/probes/verifier_storage_observer.c','-o',observer],check=True)
            observed=link(work,prof_app,prof_runtime,'observed',observer)
            sections=subprocess.check_output(['size','-A',observer],text=True)
            observer_bss=int(re.search(r'(?m)^\.bss\s+(\d+)',sections).group(1))
            manifest={'source_manifest':initial,'source_symbols':symbols_global,'descriptors':types,
                      'compiler_assembly_sha256':hashlib.sha256(app.encode()).hexdigest(),
                      'runtime_sha256':hashlib.sha256(runtime.encode()).hexdigest(),
                      'plain_binary_sha256':sha(plain),'observer_binary_sha256':sha(observed),
                      'record_size':RECORD_SIZE,'cap_seconds':a.cap,
                      'observer_bss_bytes':observer_bss,
                      'observer_sections':sections,
                      'physical_record_order':'current compiler reverses nominal source field order; checked source schemas and runtime type/shape/formula invariants',
                      'scope':'actual allocated block capacity including 32-byte headers; source-site lifetime and independent semantic backing snapshots; observer maps are not GC roots; not RSS',
                      'post_output_gc_audit':'two diagnostic-only collections after entry completes; excluded from normal execution boundaries',
                      'workloads':{}}
            (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
            for module in ['typed_ir.eri']+(['ir_verify.eri'] if a.large else []):
                target=ROOT/'src/compiler'/module;folder=output/module;folder.mkdir(exist_ok=True)
                ref=folder/'reference.s';r=run([frontend,'emit-asm',target,'--source-root',ROOT/'src'],ref,folder/'reference.stderr',a.cap)
                if r['status']!='completed':raise AssertionError('independent reference missing')
                for name,exe in [('plain',plain),('observed',observed)]:
                    if module=='ir_verify.eri' and name=='plain' and a.large_observer_only:
                        (folder/'plain.json').write_text(json.dumps({'status':'not-rerun','reason':'unchanged production large workload already censored at 90s in round three'},indent=2)+'\n')
                        continue
                    stream.seek(0);stream.truncate(0)
                    out=folder/(name+'.s');err=folder/(name+'.stderr')
                    result=run([exe,'emit-asm',target,'--source-root',ROOT/'src'],out,err,a.cap,
                               fd=stream.fileno() if name=='observed' else None)
                    if result['status']=='completed':
                        if out.read_bytes()!=ref.read_bytes() or err.read_bytes():raise AssertionError('independent output parity failed')
                        result['independent_assembly_parity']=True
                    if name=='observed':
                        stream.flush();raw=output/'records.bin'
                        shutil.copyfile(raw,folder/'records.bin')
                        result['records']=records(raw)
                        result['record_count']=len(result['records'])
                        if not result['records']:raise AssertionError('no storage snapshots')
                    (folder/(name+'.json')).write_text(json.dumps(result,indent=2)+'\n')
                    print(module,name,result['status'],result.get('record_count',''),flush=True)
                manifest['workloads'][module]={'source_sha256':sha(target),'reference_sha256':sha(ref)}
                (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
            if a.fixtures:
                fixture_root=work/'fixture-src';fixture_root.mkdir()
                shutil.copytree(ROOT/'src/compiler',fixture_root/'compiler')
                for width,chains in [(1,0),(61,0),(62,0),(62,4),(126,8),(2008,297)]:
                    name=f'fixture-{width}-{chains}';folder=output/name;folder.mkdir(exist_ok=True)
                    entry=fixture_root/'main.eri';entry.write_text(benchmark_program(width,chains,2))
                    reference=work/(name+'-C')
                    if build_native(entry,reference,fixture_root,cc=os.environ.get('CC','gcc')):raise AssertionError('fixture C build failed')
                    c_result=subprocess.run([reference],capture_output=True,timeout=a.cap)
                    if (c_result.returncode,c_result.stdout,c_result.stderr)!=(0,b'2\n',b''):raise AssertionError('independent fixture oracle')
                    emitted=subprocess.run([frontend,'emit-asm',entry,'--source-root',fixture_root,'--trace-phases'],capture_output=True,text=True,timeout=a.cap)
                    if emitted.returncode:raise AssertionError(emitted.stderr[-1000:])
                    fa,fr=instrument(emitted.stdout,emitted.stderr,runtime)
                    ft=descriptors(emitted.stdout)
                    fo=work/(name+'-observer.o')
                    command=[os.environ.get('CC','gcc'),'-std=c11','-O2','-ffreestanding','-fno-builtin','-fno-stack-protector','-fno-pie','-mgeneral-regs-only',
                             *[f'-D{k}={v}' for k,v in ft.items()],f'-DOUTPUT_FD={stream.fileno()}','-c',
                             ROOT/'tools/probes/verifier_storage_observer.c','-o',fo]
                    subprocess.run(command,check=True)
                    expected_r=1+width+chains;expected_b=4+chains
                    expected_n=(2*expected_b+1)*((expected_r+61)//62)
                    for label,aa,rr,oo in [('plain',emitted.stdout,runtime,None),('observed',fa,fr,fo)]:
                        exe=link(work,aa,rr,name+'-'+label,oo);stream.seek(0);stream.truncate(0)
                        out=folder/(label+'.stdout');err=folder/(label+'.stderr')
                        result=run([exe],out,err,a.cap,fd=stream.fileno() if oo else None)
                        if result['status']!='completed' or out.read_bytes()!=b'2\n' or err.read_bytes():raise AssertionError('fixture output parity')
                        if oo:
                            stream.flush();shutil.copyfile(output/'records.bin',folder/'records.bin')
                            result['records']=records(output/'records.bin')
                            snapshots=[r for r in result['records'] if r['event'] in (1,2)]
                            if len(snapshots)!=4 or any((r['registers'],r['blocks'],r['mask_words'])!=(expected_r,expected_b,expected_n) for r in snapshots):raise AssertionError('independent fixture R/B/N census mismatch')
                            final=[r for r in result['records'] if r['event']==6]
                            if not final or any(r['aggregate']['live'] for r in final):raise AssertionError('fixture allocations not completely reclaimed')
                        (folder/(label+'.json')).write_text(json.dumps(result,indent=2)+'\n')
                    manifest['workloads'][name]={'width':width,'chains':chains,'registers':expected_r,'blocks':expected_b,'mask_words':expected_n,'rounds':2,
                        'app_sha256':hashlib.sha256(emitted.stdout.encode()).hexdigest(),'descriptors':ft,'independent_C_plain_observer_output':'2\n'}
                    print(name,'actual storage + independent census + complete reclamation PASS',flush=True)
                    if width==1:
                        for control in ('wrong-graph-kind','observer-bound'):
                            cs=(ROOT/'tools/probes/verifier_storage_observer.c').read_text()
                            cs=cs.replace('void st_select_graph(void) { st_kind=1; }','void st_select_graph(void) { st_kind=0; }') if control=='wrong-graph-kind' else cs.replace('#define MAX_IDS 512','#define MAX_IDS 2')
                            cpath=work/(control+'.c');cpath.write_text(cs)
                            control_obj=work/(control+'.o');control_command=list(command)
                            control_command[-3]=cpath;control_command[-1]=control_obj
                            subprocess.run(control_command,check=True)
                            exe=link(work,fa,fr,control,control_obj);stream.seek(0);stream.truncate(0)
                            result=run([exe],folder/(control+'.stdout'),folder/(control+'.stderr'),a.cap,fd=stream.fileno())
                            if result.get('returncode')!=125:raise AssertionError('observer negative control did not fail closed')
                            stream.flush();raw=(output/'records.bin').read_bytes()
                            if len(raw)<RECORD_SIZE or struct.unpack_from('<Q',raw,8)[0]!=99:raise AssertionError('missing observer refusal record')
                            manifest.setdefault('negative_controls',{})[control]={'returncode':125,'observer_error_record':True}
                    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    if initial!={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'src').rglob('*.eri'))}:raise AssertionError('production sources changed')
    manifest['source_snapshot_unchanged']=True
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

if __name__=='__main__':main()
