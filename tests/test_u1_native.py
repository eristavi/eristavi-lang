"""Real native binary64/FFI execution from independently verified Eristavi UIR.

Expected Float results come from the existing integer/Fraction IEEE oracle,
not host doubles or the C adapter. No full compiler self-build is performed.
"""
import copy
import hashlib
import json
import itertools
import os
from pathlib import Path
import platform
import random
import shlex
import shutil
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native
from test_u1_promotion import (_FLOAT_SAMPLES, _SIGN, _U64, _oracle_float_binary,
                               _oracle_float_cmp)
ROOT=Path(__file__).resolve().parents[1]
RUNNER=r'''
int main(void) {
    unsigned target,ambient; uint64_t a,b;
    while(scanf("%u %" SCNx64 " %" SCNx64 " %u",&target,&a,&b,&ambient)==4) {
        u1_environment saved=u1_fp_save(),hostile=saved;
#if defined(__x86_64__)
        hostile.control=0x1f80 | (ambient%4)*0x2000 | (ambient?0x8040:0);
#else
        hostile.control=(uint64_t)(ambient%4)<<22 | (ambient?UINT64_C(1)<<24:0);
        hostile.status=ambient?31:0;
#endif
        u1_fp_restore(hostile);
        uint64_t in[2]={a,b},out[40]={0};FILE *stream=tmpfile();
        if(!stream)return 8;
        int cancelled=ambient==8;
        u1_context ctx={.fuel=ambient==9?1:10000,.capacity=ambient==10?1:1048576,
            .traffic_limit=1048576,.depth_limit=64,.cancelled=&cancelled,
            .output=ambient==11?NULL:stream};
        size_t count=(target==5||target==6||target==8)?1:2;
        u1_result result=u1_run(&u1_image,target,in,count,out,40,&ctx);
        u1_environment after=u1_fp_save();
        if(after.control!=hostile.control)return 9;
#if defined(__aarch64__)
        if(after.status!=hostile.status)return 10;
#endif
        u1_fp_restore(saved);
        if(ctx.live)return 11;
        printf("%d %d %" PRId64 " %zu",result.kind,result.code,result.location,result.count);
        for(size_t i=0;i<result.count;i++)printf(" %016" PRIx64,out[i]);
        const int64_t *loc=u1_trap_location(&u1_image,result);
        printf(" | %" PRId64 " |",loc?loc[4]:0);
        rewind(stream);int ch;
        while((ch=fgetc(stream))!=EOF)putchar(ch=='\n'?',':ch);
        printf(" | %" PRIu64 " %" PRIu64 "\n",ctx.peak,ctx.traffic);fclose(stream);
    }
    return ferror(stdin)?12:0;
}
'''

@unittest.skipUnless(platform.machine().lower() in ('x86_64','amd64','aarch64','arm64'),
                     'native U1a supports x86-64/AArch64')
class U1NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name)
        (cls.root/'compiler').symlink_to(ROOT/'src/compiler',target_is_directory=True)
        source=cls.root/'native.eri';source.write_text((ROOT/'tests/fixtures/u1_native.eri').read_text())
        cls.emitter=cls.root/'emitter'
        if build_native(source,cls.emitter,cls.root):raise AssertionError('UIR native fixture compilation failed')
        result=subprocess.run([str(cls.emitter),'emit'],capture_output=True,text=True,timeout=30)
        if result.returncode or result.stderr:raise AssertionError(result.stdout+result.stderr)
        cls.image=result.stdout;path=cls.root/'image.c';path.write_text(cls.image+RUNNER)
        cls.binary=cls.root/'native'
        cls.cc=shlex.split(os.environ.get('CC','cc'))
        cmd=cls.cc+['-std=c11','-O2','-ffp-contract=off','-fno-fast-math','-I',str(ROOT/'runtime'),
                    str(path),'-o',str(cls.binary)]
        subprocess.run(cmd,check=True,capture_output=True,text=True,timeout=60)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def run_cases(self,cases,binary=None):
        text=''.join(f'{target} {a&_U64:x} {b&_U64:x} {ambient}\n'
                     for target,a,b,ambient in cases)
        result=subprocess.run([str(binary or self.binary)],input=text,capture_output=True,text=True,timeout=30)
        self.assertEqual((result.returncode,result.stderr),(0,''),result.stdout[-1000:])
        observations=[]
        for line in result.stdout.splitlines():
            status,location,trace,resources=line.split(' |')
            values=status.split();kind,code,loc,count=map(int,values[:4])
            words=tuple(int(value,16) for value in values[4:])
            self.assertEqual(len(words),count)
            peak,traffic=map(int,resources.split())
            self.assertLessEqual(peak,traffic)
            self.assertLessEqual(peak,1048576)
            observations.append(((kind,code,loc,count),words,int(location),trace.strip()))
        self.assertEqual(len(observations),len(cases))
        return observations

    def test_native_float_rational_oracle_and_hostile_environments(self):
        rng=random.Random(0xF64)
        samples=_FLOAT_SAMPLES+(0x7ff0000000000001,0xfff8000000000042,
            0x3ca0000000000000,0x3cb0000000000000,0x0010000000000001)
        pairs=list(itertools.product(samples,repeat=2))
        pairs += [(rng.getrandbits(64),rng.getrandbits(64)) for _ in range(120)]
        # Explicit halfway ties, underflow ties, largest subnormal -> normal,
        # overflow and negative-zero division; all modes include FTZ/DAZ hostility.
        pairs += [(0x3ff0000000000000,0x3ca0000000000000),
                  (0x3ff0000000000001,0x3ca0000000000000),(1,0x4000000000000000),
                  (3,0x4000000000000000),(0x000fffffffffffff,1)]
        cases=[(1,a,b,i%4) for i,(a,b) in enumerate(pairs)]
        for (a,b),observed in zip(pairs,self.run_cases(cases)):
            expected=tuple(_oracle_float_binary(a,b,op)&_U64 for op in range(28,32))
            expected+=(a^_SIGN,)
            expected+=tuple(int(_oracle_float_cmp(a,b,relation)) for relation in range(1,7))
            expected+=(0,)  # Separate multiply/add must not fuse.
            self.assertEqual(observed,((0,0,0,12),expected,0,''),(hex(a),hex(b)))

    def test_native_production_imports_fault_origins_limits_and_strip(self):
        cases=[(2,7,3,0),(2,7,0,3),(2,-(1<<63),-1,2),(2,-7,3,1),
               (5,7,0,0),(1,0,0,8),(1,0,0,9),(1,0,0,10),(2,7,3,11)]
        results=self.run_cases(cases)
        self.assertEqual(results[0],((0,0,0,1),(2,),0,'7,3,'))
        self.assertEqual(results[1],((1,2,3,0),(),2,'7,'))
        self.assertEqual(results[2],((1,1,3,0),(),2,'-9223372036854775808,'))
        self.assertEqual(results[3],((0,0,0,1),((-2)&_U64,),0,'-7,3,'))
        self.assertEqual(results[4],((0,0,0,1),((-(1<<63)+7)&_U64,),0,''))
        for result in results[5:8]:self.assertEqual(result[0][0],2)
        self.assertEqual(results[8],((1,4,1,0),(),1,''))
        if shutil.which('strip'):
            stripped=self.root/'stripped';shutil.copy2(self.binary,stripped)
            subprocess.run(['strip',str(stripped)],check=True,capture_output=True,timeout=15)
            self.assertEqual(self.run_cases(cases,stripped),results)

    def test_publication_invalidation_and_transactional_simplification(self):
        result=subprocess.run([str(self.emitter)],capture_output=True,text=True,timeout=30)
        self.assertEqual((result.returncode,result.stdout,result.stderr),
            (0,'publication-exact-content:ok\ntransactional-folding:ok\n'
             'source-import-revision-rejection:ok\npublication-quota-cleanup:ok\n'
             'simplification-dead-cfg-cancellation:ok\n',''))

    def test_native_recursion_and_independent_simplification(self):
        cases=[(6,n,0,n%4) for n in (0,1,2,7,15,30)]+[(6,-1,0,0)]
        results=self.run_cases(cases)
        for case,result in zip(cases[:-1],results[:-1]):
            self.assertEqual(result,((0,0,0,1),(case[1],),0,''))
        self.assertEqual(results[-1][0][0],2)
        original=subprocess.run([str(self.emitter),'original'],capture_output=True,text=True,timeout=30)
        self.assertEqual((original.returncode,original.stderr),(0,''),original.stdout[-1000:])
        path=self.root/'original.c';path.write_text(original.stdout+RUNNER)
        binary=self.root/'original'
        subprocess.run(self.cc+['-std=c11','-O2','-I',str(ROOT/'runtime'),str(path),'-o',str(binary)],
            check=True,capture_output=True,text=True,timeout=30)
        rng=random.Random(77)
        cases=[(5,n,0,i%4) for i,n in enumerate([0,1,-1,-(1<<63),(1<<63)-1]+
             [rng.getrandbits(64) for _ in range(40)])]
        self.assertEqual(self.run_cases(cases),self.run_cases(cases,binary))

    def test_native_integer_oracle_multivalue_and_parallel_switch_edges(self):
        from test_u1_integer_execution import BOUNDARIES, expected
        modes=(3,15,16,17,19,20,21,22,23,24,25,26,27)
        pairs=[(a,b) for a,b in itertools.product(BOUNDARIES,repeat=2)
               if b and (a,b)!=(-(1<<63),-1)]
        results=self.run_cases([(9,a,b,i%4) for i,(a,b) in enumerate(pairs)])
        for (a,b),result in zip(pairs,results):
            words=[]
            for mode in modes:
                status,_=expected(mode,a,b)
                words.append(status[4]&_U64)
                if mode in (3,19,20,21,22,23):words.append(status[5])
            for relation in range(1,11):words.append(expected(100+relation,a,b)[0][5])
            self.assertEqual(result,((0,0,0,len(words)),tuple(words),0,''))
        pairs=list(itertools.product((0,1,-1,-(1<<63),(1<<63)-1),(-7,5)))
        results=self.run_cases([(10,a,b,i%4) for i,(a,b) in enumerate(pairs)])
        for (a,b),result in zip(pairs,results):
            wanted=a if a in (-(1<<63),(1<<63)-1) else b
            self.assertEqual(result,((0,0,0,1),(wanted&_U64,),0,''))
        for a,b in [(0,0),(_SIGN,1),(0x7ff8000000000000,0x3ff0000000000000)]:
            self.assertEqual(*self.run_cases([(1,a,b,3),(7,a,b,2)]))
        result=self.run_cases([(8,42,0,1)])[0]
        self.assertEqual(result,((0,0,0,0),(),0,'42,'))

    def test_source_map_ingress_remap_and_stale_excerpt(self):
        from compiler.erist.u1_source_map import Source, SourceMap
        result=subprocess.run([str(self.emitter),'map'],capture_output=True,timeout=30)
        self.assertEqual((result.returncode,result.stderr),(0,b''))
        raw=json.loads(result.stdout)
        digest='0123456789abcdef'*4
        expected={'native-probe':(digest,64)}
        decoded=SourceMap.decode(result.stdout,expected)
        self.assertEqual(decoded.locations[2].parents,((2,0),(1,2),(2,3)))
        self.assertEqual(decoded.locations[2].line,2)
        mapped,ids=decoded.remap({Source('other','0'*64,1):1048576},start=7)
        self.assertEqual(ids,(7,))
        self.assertEqual(len(mapped),2) # sparse external IDs never size an array
        for key,value in [('native_contract',2),('schema',2)]:
            altered=copy.deepcopy(raw);altered[key]=value
            with self.assertRaises(ValueError):SourceMap.decode(json.dumps(altered).encode(),expected)
        for table,index,value in [('origins',1,3),('locations',20,4*1048577+3),
                                  ('bytes',raw['sources'][2],49),('sources',3,65)]:
            altered=copy.deepcopy(raw);altered[table][index]=value
            with self.assertRaises(ValueError):SourceMap.decode(json.dumps(altered).encode(),expected)
        with self.assertRaises(ValueError):SourceMap.decode(result.stdout,{'native-probe':('0'*64,64)})
        with self.assertRaises(ValueError):decoded.sources[0].excerpt(b'changed',0,1)
        content='aα\nsecond'.encode()
        source=Source('module/file.eri',hashlib.sha256(content).hexdigest(),len(content))
        self.assertEqual(source.excerpt(content,1,3),'α')
        with self.assertRaises(ValueError):source.excerpt(b'x'*len(content),1,3)
        with self.assertRaises(ValueError):SourceMap.decode(b'{"schema":1,"schema":1}',{})

    def test_changed_foreign_floating_environment_is_rejected_and_restored(self):
        # Model a hostile host stdio implementation. It is outside the closed
        # UIR import catalog; the imported-call boundary must still reject it.
        prefix='#include <stdio.h>\nint hostile_fprintf(FILE*,const char*,...);\n#define fprintf hostile_fprintf\n'
        suffix=r"""
#undef fprintf
#include <stdarg.h>
int hostile_fprintf(FILE *file,const char *format,...) {
    va_list args;va_start(args,format);int written=vfprintf(file,format,args);va_end(args);
    u1_environment env=u1_fp_save();
#if defined(__x86_64__)
    env.control^=0x2000;
#else
    env.control^=UINT64_C(1)<<22;
#endif
    u1_fp_restore(env);return written;
}
"""
        path=self.root/'hostile.c';path.write_text(prefix+self.image+suffix+RUNNER)
        binary=self.root/'hostile'
        subprocess.run(self.cc+['-std=c11','-O2','-I',str(ROOT/'runtime'),str(path),'-o',str(binary)],
            check=True,capture_output=True,text=True,timeout=30)
        result=self.run_cases([(2,7,3,3)],binary)[0]
        self.assertEqual(result,((4,4,1,0),(),1,'7,'))

    def test_test_only_imports_cannot_authorize_production_native_execution(self):
        result=subprocess.run([str(self.emitter),'test-import'],capture_output=True,text=True,timeout=30)
        self.assertEqual((result.returncode,result.stdout,result.stderr),
            (1,'test imports cannot authorize native production calls\n',''))

    def test_native_adapter_rejects_fast_math(self):
        path=self.root/'unsafe.c';path.write_text('#include "u1_native.h"\n')
        result=subprocess.run(self.cc+['-std=c11','-ffast-math','-I',str(ROOT/'runtime'),
            '-c',str(path),'-o',str(self.root/'unsafe.o')],capture_output=True,text=True,timeout=30)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('cannot use fast-math',result.stderr)

if __name__=='__main__':unittest.main()
