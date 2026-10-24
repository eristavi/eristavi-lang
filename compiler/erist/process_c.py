"""Portable hosted process boundary for the C bootstrap executable."""
PROCESS_RUNTIME = r'''
static int eri_process_argc=0;
static char **eri_process_argv=NULL;
static int eri_process_exit_code=0;
static eri_list_text eri_process_arguments(void){
    size_t count=eri_process_argc>0 ? (size_t)eri_process_argc-1 : 0;
    eri_list_text result={count,NULL};
    if(count>SIZE_MAX/sizeof(eri_text))eri_fault("too many process arguments");
    if(count)result.data=(eri_text*)eri_alloc(count*sizeof(eri_text));
    for(size_t i=0;i<count;i++){
        const unsigned char *data=(const unsigned char*)eri_process_argv[i+1];
        size_t length=strlen((const char*)data);
        if(!eri_utf8_valid(data,length))eri_fault("process arguments must be valid UTF-8");
        result.data[i]=eri_text_from_bytes(data,length);
    }
    return result;
}
static void eri_process_writeError(eri_text text){
    if(text.len)fwrite(text.data,1,text.len,stderr);
    fputc('\n',stderr);
}
static void eri_process_setExitCode(int64_t code){
    if(code<0||code>255)eri_fault("process exit code must be between 0 and 255");
    eri_process_exit_code=(int)code;
}
'''
