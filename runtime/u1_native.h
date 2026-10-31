/* Private U1a native execution adapter, revision 1. Not the production ABI.
 * Only compiler.u1_native's freshly verified, exact publication may emit tables.
 * There is no serialized ready/trusted flag or arbitrary FFI callback interface.
 */
#ifndef ERIST_U1_NATIVE_H
#define ERIST_U1_NATIVE_H
#define ERIST_U1_NATIVE_CONTRACT 1
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <inttypes.h>
#include <limits.h>
#include <float.h>
#if defined(__FAST_MATH__)
#error U1 strict binary64 cannot use fast-math
#endif
_Static_assert(sizeof(double)==8 && DBL_MANT_DIG==53 && DBL_MAX_EXP==1024,
               "U1 requires IEEE binary64");
#if defined(__x86_64__)
typedef struct { uint32_t control; } u1_environment;
static inline u1_environment u1_fp_save(void) {
    u1_environment env; __asm__ volatile("stmxcsr %0" : "=m"(env.control)); return env;
}
static inline void u1_fp_restore(u1_environment env) {
    __asm__ volatile("ldmxcsr %0" : : "m"(env.control) : "memory");
}
static inline void u1_fp_enter(void) { u1_environment env={0x1f80}; u1_fp_restore(env); }
static inline int u1_fp_valid(void) { return (u1_fp_save().control & ~UINT32_C(63))==0x1f80; }
#elif defined(__aarch64__)
typedef struct { uint64_t control, status; } u1_environment;
static inline u1_environment u1_fp_save(void) {
    u1_environment env;
    __asm__ volatile("mrs %0, fpcr\n\tmrs %1, fpsr" : "=r"(env.control),"=r"(env.status));
    return env;
}
static inline void u1_fp_restore(u1_environment env) {
    __asm__ volatile("msr fpcr, %0\n\tmsr fpsr, %1\n\tisb" : : "r"(env.control),"r"(env.status) : "memory");
}
static inline void u1_fp_enter(void) { u1_environment env={0,0}; u1_fp_restore(env); }
static inline int u1_fp_valid(void) { return u1_fp_save().control==0; }
#else
#error U1 native revision 1 supports only x86-64 and AArch64
#endif
static inline int u1_nan(uint64_t bits) {
    return (bits & UINT64_C(0x7fffffffffffffff)) > UINT64_C(0x7ff0000000000000);
}
/* Integer ordering handles quiet/signaling NaN without raising FP exceptions. */
static inline uint64_t u1_float_cmp(uint64_t a,uint64_t b,int relation) {
    if (u1_nan(a)||u1_nan(b)) return relation==2;
    int equal=a==b || ((a|b)&UINT64_C(0x7fffffffffffffff))==0;
    uint64_t ka=(a>>63) ? ~a : a^UINT64_C(0x8000000000000000);
    uint64_t kb=(b>>63) ? ~b : b^UINT64_C(0x8000000000000000);
    int less=!equal && ka<kb;
    switch (relation) {
        case 1:return equal; case 2:return !equal; case 3:return less;
        case 4:return equal||less; case 5:return !equal&&!less; case 6:return !less;
    }
    return 0;
}
static inline uint64_t u1_float(int op,uint64_t a,uint64_t b,int relation) {
    if (op==32) return a^UINT64_C(0x8000000000000000);
    if (op==33) return u1_float_cmp(a,b,relation);
    double x,y; memcpy(&x,&a,8); memcpy(&y,&b,8);
#if defined(__x86_64__)
    switch(op) {
        case 28: __asm__ volatile("addsd %1,%0" : "+x"(x) : "x"(y)); break;
        case 29: __asm__ volatile("subsd %1,%0" : "+x"(x) : "x"(y)); break;
        case 30: __asm__ volatile("mulsd %1,%0" : "+x"(x) : "x"(y)); break;
        case 31: __asm__ volatile("divsd %1,%0" : "+x"(x) : "x"(y)); break;
    }
#else
    switch(op) {
        case 28: __asm__ volatile("fadd %d0,%d0,%d1" : "+w"(x) : "w"(y)); break;
        case 29: __asm__ volatile("fsub %d0,%d0,%d1" : "+w"(x) : "w"(y)); break;
        case 30: __asm__ volatile("fmul %d0,%d0,%d1" : "+w"(x) : "w"(y)); break;
        case 31: __asm__ volatile("fdiv %d0,%d0,%d1" : "+w"(x) : "w"(y)); break;
    }
#endif
    uint64_t result; memcpy(&result,&x,8);
    return u1_nan(result)?UINT64_C(0x7ff8000000000000):result;
}
typedef struct {
    const int64_t *blocks,*instructions,*operands,*edges,*arguments,*switches,*cases;
    const int64_t *parameters;
    size_t values,scratch,parameter_count,result_count;
    int adapter;
} u1_function;
typedef struct {
    const u1_function *functions; size_t count;
    const int64_t *locations,*origins; size_t location_count,origin_count;
    const int64_t *sources,*source_bytes; size_t source_count;
} u1_program;
typedef struct { int kind,code; int64_t location; size_t count; } u1_result;
typedef struct {
    uint64_t fuel,live,peak,traffic,capacity,traffic_limit;
    unsigned depth_limit; volatile const int *cancelled; FILE *output;
} u1_context;
static inline u1_result u1_status(int kind,int code,int64_t loc,size_t count) {
    u1_result result={kind,code,loc,count}; return result;
}
static inline int64_t u1_signed(uint64_t word) { int64_t value; memcpy(&value,&word,8); return value; }
static inline int u1_work(u1_context *ctx,uint64_t count) {
    if ((ctx->cancelled && *ctx->cancelled) || count>ctx->fuel) return 0;
    ctx->fuel-=count; return 1;
}
static inline uint64_t u1_compare(uint64_t a,uint64_t b,int rel) {
    int64_t x=u1_signed(a),y=u1_signed(b);
    switch(rel) {
        case 1:return a==b; case 2:return a!=b; case 3:return x<y;
        case 4:return x<=y; case 5:return x>y; case 6:return x>=y;
        case 7:return a<b; case 8:return a<=b; case 9:return a>b; case 10:return a>=b;
    }
    return 0;
}
static u1_result u1_invoke(const u1_program *program,size_t target,const uint64_t *inputs,
    size_t count,uint64_t *outputs,u1_context *ctx,unsigned depth,int64_t site) {
    if (depth>ctx->depth_limit || !u1_work(ctx,1)) return u1_status(2,0,site,0);
    if (!target || target>program->count) return u1_status(4,1,site,0);
    const u1_function *fn=program->functions+target-1;
    if (count!=fn->parameter_count) return u1_status(4,2,site,0);
    for (size_t i=0;i<count;i++) {
        if (!u1_work(ctx,1)) return u1_status(2,0,site,0);
        if (fn->parameters[i]==1 && inputs[i]>1) return u1_status(4,3,site,0);
    }
    if (fn->adapter) {
        /* Trusted catalog: no callback pointer, symbol lookup or caller effect mask. */
        if (!u1_fp_valid()) return u1_status(4,4,site,0);
        if (fn->adapter==3) { outputs[0]=inputs[0]; return u1_status(0,0,0,1); }
        if (fn->adapter==4) {
            int failed=!ctx->output || fprintf(ctx->output,"%" PRId64 "\n",u1_signed(inputs[0]))<0;
            if (!u1_fp_valid()) return u1_status(4,4,site,0);
            return u1_status(failed?1:0,failed?4:0,failed?site:0,0);
        }
        return u1_status(3,34,site,0);
    }
    if (fn->values>SIZE_MAX/8-1 || fn->scratch>(SIZE_MAX/8-fn->values-1)/2)
        return u1_status(2,1,site,0);
    size_t slots=fn->values+1+2*fn->scratch,bytes=slots*8;
    if (ctx->live>ctx->capacity || bytes>ctx->capacity-ctx->live ||
        ctx->traffic>ctx->traffic_limit || bytes>ctx->traffic_limit-ctx->traffic)
        return u1_status(2,1,site,0);
    uint64_t *v=calloc(slots,8);
    if (!v) return u1_status(2,1,site,0);
    ctx->live+=bytes; ctx->traffic+=bytes;
    if (ctx->live>ctx->peak) ctx->peak=ctx->live;
    uint64_t *args=v+fn->values+1,*returns=args+fn->scratch;
    for (size_t i=0;i<count;i++) v[fn->blocks[0]+i]=inputs[i];
    size_t block=1; u1_result result=u1_status(4,5,site,0);
    for (;;) {
        size_t base=(block-1)*5;
        int64_t cursor=fn->blocks[base+2],terminal=fn->blocks[base+4];
        while (cursor || terminal) {
            if (!cursor) { cursor=terminal; terminal=0; }
            const int64_t *ins=fn->instructions+(cursor-1)*10;
            int op=(int)ins[0]; size_t first=(size_t)ins[2],n=(size_t)ins[3],r=(size_t)ins[4];
            int64_t loc=ins[6],payload=ins[7]; uint64_t a=0,b=0,answer=0,flag=0;
            if (!u1_work(ctx,1)) { result=u1_status(2,0,loc,0); goto done; }
            if (n) a=v[fn->operands[first]];
            if (n>1) b=v[fn->operands[first+1]];
            switch(op) {
                case 1:case 2:case 9:v[r]=(uint64_t)payload;break;
                case 4:v[r]=!a;break;
                case 13:v[r]=a&&b;break;case 14:v[r]=a||b;break;
                case 3:case 15:case 16:case 17:case 19:case 20:case 21:case 22:case 23:
                    if (op==3||op==15||op==21) answer=a+b;
                    else if(op==16||op==19||op==22) answer=a-b;
                    else answer=a*b;
                    if(op==3) flag=__builtin_add_overflow(u1_signed(a),u1_signed(b),&(int64_t){0});
                    if(op==19) flag=__builtin_sub_overflow(u1_signed(a),u1_signed(b),&(int64_t){0});
                    if(op==20) flag=__builtin_mul_overflow(u1_signed(a),u1_signed(b),&(int64_t){0});
                    if(op==21) flag=answer<a;
                    if(op==22) flag=a<b;
                    if(op==23) flag=b && a>UINT64_MAX/b;
                    v[r]=answer;if(ins[5]==2)v[r+1]=flag;break;
                case 18:v[r]=u1_compare(a,b,(int)payload);break;
                case 24:case 25:case 26:case 27:
                    if(!b){result=u1_status(1,2,loc,0);goto done;}
                    if(op<=25 && a==UINT64_C(0x8000000000000000) && b==UINT64_MAX) {
                        result=u1_status(1,1,loc,0);goto done;
                    }
                    if(op==24) v[r]=(uint64_t)(u1_signed(a)/u1_signed(b));
                    if(op==25) v[r]=(uint64_t)(u1_signed(a)%u1_signed(b));
                    if(op==26) v[r]=a/b;if(op==27)v[r]=a%b;break;
                case 28:case 29:case 30:case 31:case 32:case 33:
                    if(!u1_fp_valid()){result=u1_status(4,4,loc,0);goto done;}
                    v[r]=u1_float(op,a,b,(int)payload);break;
                case 5:if(!a){result=u1_status(1,(int)payload,loc,0);goto done;}break;
                case 8:
                    for(size_t i=0;i<n;i++) {
                        if(!u1_work(ctx,1)){result=u1_status(2,0,loc,0);goto done;}
                        outputs[i]=v[fn->operands[first+i]];
                    }
                    result=u1_status(0,0,0,n);goto done;
                case 34:
                    for(size_t i=0;i<n;i++) {
                        if(!u1_work(ctx,1)){result=u1_status(2,0,loc,0);goto done;}
                        args[i]=v[fn->operands[first+i]];
                    }
                    result=u1_invoke(program,(size_t)payload,args,n,returns,ctx,depth+1,loc);
                    if(result.kind)goto done;
                    if(result.count!=(size_t)ins[5]){result=u1_status(4,6,loc,0);goto done;}
                    for(size_t i=0;i<result.count;i++) {
                        if(!u1_work(ctx,1)){result=u1_status(2,0,loc,0);goto done;}
                        v[r+i]=returns[i];
                    }
                    break;
                case 6:case 7:case 35: {
                    int64_t edge=payload;
                    if(op==7&&!a)edge=ins[8];
                    if(op==35) {
                        const int64_t *sw=fn->switches+(payload-1)*3;edge=sw[2];
                        for(int64_t i=0;i<sw[1];i++) {
                            if(!u1_work(ctx,1)){result=u1_status(2,0,loc,0);goto done;}
                            if(a==(uint64_t)fn->cases[(sw[0]+i)*2]){edge=fn->cases[(sw[0]+i)*2+1];break;}
                        }
                    }
                    const int64_t *e=fn->edges+(edge-1)*3;
                    for(int64_t i=0;i<e[2];i++) {
                        if(!u1_work(ctx,1)){result=u1_status(2,0,loc,0);goto done;}
                        args[i]=v[fn->arguments[e[1]+i]];
                    }
                    size_t start=(size_t)fn->blocks[(e[0]-1)*5];
                    for(int64_t i=0;i<e[2];i++)v[start+i]=args[i];
                    block=(size_t)e[0];cursor=terminal=0;continue;
                }
                default:result=u1_status(3,op,loc,0);goto done;
            }
            cursor=ins[9];
        }
    }
done:
    free(v);ctx->live-=bytes;return result;
}
static u1_result u1_run(const u1_program *program,size_t target,const uint64_t *inputs,
    size_t count,uint64_t *outputs,size_t output_capacity,u1_context *ctx) {
    if (!ctx || !program || !target || target>program->count || !ctx->depth_limit ||
        ctx->depth_limit>256 || ctx->fuel>1048576 ||
        program->functions[target-1].result_count>output_capacity ||
        (count && !inputs) || (output_capacity && !outputs)) return u1_status(4,7,0,0);
    u1_environment caller=u1_fp_save();u1_fp_enter();
    u1_result result=u1_invoke(program,target,inputs,count,outputs,ctx,1,0);
    u1_fp_restore(caller);return result;
}
/* Required diagnostic metadata is independent of debug info and stripping. */
static const int64_t *u1_trap_location(const u1_program *program,u1_result result) {
    if(result.location<1 || (uint64_t)result.location>program->location_count)return NULL;
    return program->locations+(result.location-1)*7;
}
#endif
