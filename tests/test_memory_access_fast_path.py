"""Differential safety/ABI checks against the verified generic memory lowering."""
from pathlib import Path
import platform,shutil,subprocess,tempfile,unittest
from compiler.erist.cli import build_native
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(platform.system()=='Linux' and platform.machine().lower() in ('x86_64','amd64'),'Linux x86-64 helpers')
class MemoryAccessFastPathTests(unittest.TestCase):
 def test_fast_accesses_match_generic_bounds_alignment_overflow_and_results(self):
  if not all(shutil.which(t) for t in ('as','ld','cc')):self.skipTest('native tools unavailable')
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);shutil.copytree(ROOT/'src/compiler',d/'compiler');shutil.copytree(ROOT/'src/runtime',d/'runtime')
   prefix='''import compiler.runtime_memory_ir as r; import compiler.runtime_memory_x86 as x; import runtime.linux_x86_64 as linux;
function program(width Int, store Bool, generic Bool) returns identity r.Program {
 let p be r.load8Program(); if store { p=r.store8Program(); }
 let cursor be p.instructions;
 while cursor!=none { if cursor.kind==5 or cursor.kind==6 or cursor.kind==7 { let node be cursor; node.width=width; node.alignment=width; } cursor=cursor.next; }
 if generic {
  let regs be p.registers; while regs!=none { let node be regs; if node.next==none { node.next=identity r.Register { index=5; valueClass=7; defined=false; provenance=-1; next=none; }; regs=none; } else { regs=node.next; } }
  let code be p.instructions; while code!=none { let node be code; if node.next==none { node.next=identity r.Instruction { kind=1; result=5; extra=-1; first=-1; second=-1; third=-1; number=123; width=0; alignment=0; next=none; }; code=none; } else { code=node.next; } }
 }
 return p;
}
output(linux.memorySource());
'''
   for w in (1,2,4,8):
    for store in (False,True):
     n=f'{"store" if store else "load"}{w}';result=3 if store else 4
     for generic in (False,True):prefix+=f'output(x.emit(program({w},{str(store).lower()},{str(generic).lower()}),"{n}_{"generic" if generic else "fast"}",{result}));\n'
   src=d/'main.eri';src.write_text(prefix);gen=d/'generator';self.assertEqual(build_native(src,gen,d),0)
   v=subprocess.run([gen],capture_output=True,text=True,timeout=20);self.assertEqual((v.returncode,v.stderr),(0,''))
   fast=v.stdout
   self.assertNotIn('pushq',fast.split('load8_fast:\n')[1].split('.size load8_fast')[0])
   body='.text\n.globl _start\n_start:\n movl $8192,%edi\n call erist_rt_reserve\n testq %rax,%rax\n je fail\n movq %rax,%r12\n'
   cases=[('base',4096,0),('base',4096,4088),('base',4096,4089),('base',4096,4095),('base',4096,4096),('base',4096,-1),('base',0,0),('base',-4096,0),('base',1,0),('base',4095,0),('base',4097,0),('null',4096,0),('overflow',4096,16)]
   for w in (1,2,4,8):
    for st in ('store','load'):
     for base,length,offset in cases:
      args=('movq %r12,%rdi' if base=='base' else f'movq ${0 if base=="null" else -8},%rdi')+f'\n movq ${length},%rsi\n movq ${offset},%rdx\n movabsq $0xfedcba9876543210,%rcx\n'
      body+=' '+args+f' call {st}{w}_fast\n movq %rax,saved_result(%rip)\n movq %rdx,saved_status(%rip)\n '+args+f' call {st}{w}_generic\n cmpq saved_result(%rip),%rax\n jne fail\n cmpq saved_status(%rip),%rdx\n jne fail\n'
   body+=' movq %r12,%rdi\n movl $8192,%esi\n call erist_rt_release\n testq %rax,%rax\n jne fail\n xorl %edi,%edi\n jmp erist_rt_exit\nfail:\n movl $99,%edi\n jmp erist_rt_exit\n.bss\n.p2align 3\nsaved_result:\n.quad 0\nsaved_status:\n.quad 0\n.section .note.GNU-stack,"",@progbits\n'
   (d/'probe.s').write_text(fast+body);subprocess.run(['as','--64',d/'probe.s','-o',d/'probe.o'],check=True,capture_output=True)
   subprocess.run(['ld','-nostdlib','-static','-e','_start',d/'probe.o','-o',d/'probe'],check=True,capture_output=True)
   v=subprocess.run([d/'probe'],capture_output=True,timeout=10);self.assertEqual((v.returncode,v.stdout,v.stderr),(0,b'',b''))
