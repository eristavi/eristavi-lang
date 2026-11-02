"""Outcome tuples and forwarded SSA values share canonical edge pools."""
import unittest
import os
import platform
import test_u2_invoke as invoke_tests


def transfer_source(source=invoke_tests.SOURCE):
    text = source.replace('compiler.u2_invoke_build as invoke',
                          'compiler.u2_invoke_transfer as invoke')
    text = text.replace('[],[meta.i64(),meta.pred()]', '[],[meta.i64(),meta.pred(),meta.i64()]')
    text = text.replace('    let target be try meta.declaration',
                        '    let failureTuple be try sig.signature(data,graph,mp,[],[payload,i64]);\n'
                        '    let target be try meta.declaration', 1)
    text = text.replace('ab.block(fn,graph,[i64,pred])', 'ab.block(fn,graph,[i64,pred,i64])')
    text = text.replace('ab.block(fn,graph,[payload])', 'ab.block(fn,graph,[payload,i64])')
    text = text.replace('continuation.bind(', 'continuation.bindCarrying(')
    text = text.replace('normalSig,failureSig,loc)', 'normalSig,failureTuple,loc)')
    text = text.replace('contract,pair,[input])', 'contract,pair,[input],[input])')
    text = text.replace('contract,uncalledPair,[input])', 'contract,uncalledPair,[input],[input])')
    hook = '''
    let carriedSlot be first+2;
    let carriedValue be try words.get(fn.arguments,rp,carriedSlot);
    try check(carriedValue == input.index,"carried value missing from canonical edge");
    fn.arguments.frozen=false; try words.set(fn.arguments,rp,carriedSlot,normalValue.index); fn.arguments.frozen=true;
    try check(try rejected(fn,graph,contract,4),"successor-defined transfer escaped predecessor availability");
    fn.arguments.frozen=false; try words.set(fn.arguments,rp,carriedSlot,0-1); fn.arguments.frozen=true;
    try check(try rejected(fn,graph,contract,2),"fresh outcome marker accepted as a forwarded value");
    fn.arguments.frozen=false; try words.set(fn.arguments,rp,carriedSlot,carriedValue); fn.arguments.frozen=true;
    let failedFirst be try words.get(fn.edges,rp,(failedEdge-1)*3+1);
    let failedSlot be failedFirst+1;
    fn.arguments.frozen=false; try words.set(fn.arguments,rp,failedSlot,errorValue.index); fn.arguments.frozen=true;
    try check(try rejected(fn,graph,contract,2),"wrong-type failure transfer accepted");
    fn.arguments.frozen=false; try words.set(fn.arguments,rp,failedSlot,input.index); fn.arguments.frozen=true;
'''
    return text.replace('    let marker be try words.get(fn.arguments,rp,first);',
                        hook + '\n    let marker be try words.get(fn.arguments,rp,first);', 1)


def reference_transfer_source():
    source = transfer_source(invoke_tests.U2InvokeTests().reference_source())
    source = source.replace('    let pair be try continuation.bindCarrying',
                            '    let normalCarry be try build.parameter(fn,normal,2);\n'
                            '    let failureCarry be try build.parameter(fn,failure,1);\n'
                            '    let pair be try continuation.bindCarrying', 1)
    source = source.replace('normal,[normalValue],loc)', 'normal,[normalCarry],loc)')
    return source.replace('failure,[failedValue],loc)', 'failure,[failureCarry],loc)')


class U2InvokeTransferTests(unittest.TestCase):
    def test_predecessor_values_follow_each_typed_outcome_with_dominance(self):
        invoke_tests.U2InvokeTests().compile_probe(transfer_source())

    def test_reference_executes_carried_values_on_success_and_failure(self):
        invoke_tests.U2InvokeTests().compile_probe(reference_transfer_source())

    @unittest.skipUnless(os.environ.get('ERISTAVI_U2_INVOKE_NATIVE') == '1' and
        platform.system() == 'Linux' and platform.machine().lower() in ('x86_64','amd64'),
        'opt-in Linux x86-64 owned-runtime transfer probe')
    def test_owned_runtime_preserves_outcome_transfers(self):
        text = reference_transfer_source().replace(
            '[0,7,9223372036854775807,-1,-19,(0-9223372036854775807-1)]', '[7,-1]')
        invoke_tests.U2InvokeTests().owned_probe(text, 'u2-invoke-transfer-owned.json')
