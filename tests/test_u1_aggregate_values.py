"""Independent immutable-value oracle against the isolated U1b reference engine.

U1b operation semantics are tested here before attaching aggregate values to
the canonical UIR. A passing test is NOT canonical make/get/set qualification.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native

ROOT = Path(__file__).resolve().parents[1]
SIZES = (2, 9, 32)


def build_program():
    statements = [
        """import std.process;
import compiler.u1_budget as budget;
import compiler.u1_meta as meta;
import compiler.u1_aggregate as aggregate;
import compiler.u1_aggregate_verify as graph_verify;
import compiler.u1_aggregate_values as values;

error ProbeError { message Text; }
function check(okay Bool, message Text) fails ProbeError {
    if not okay { fail ProbeError { message=message; }; }
}
function rejectWrongField(engine identity values.Engine, source values.ValueId)
    returns Bool fails budget.LimitError,ProbeError {
    let wrong be values.get(engine,source,100)
    else error budget.LimitError {
        try check(error.message == "aggregate field index out of range",
            "out-of-range aggregate.get");
        return true;
    };
    fail ProbeError { message="out-of-range aggregate field was accepted"; };
}
function rejectWrongSet(engine identity values.Engine, source values.ValueId,
    wrongValue values.ValueId)
    returns Bool fails budget.LimitError,ProbeError {
    let wrong be values.set(engine,source,0,wrongValue)
    else error budget.LimitError {
        try check(error.message == "aggregate.set replacement type mismatch",
            "static aggregate.set replacement type");
        return true;
    };
    fail ProbeError { message="incorrect aggregate.set type accepted"; };
}
function rejectWrongMake(engine identity values.Engine,shape aggregate.TypeId,
    wrongValue values.ValueId)
    returns Bool fails budget.LimitError,ProbeError {
    let wrong be values.make(engine,shape,[wrongValue])
    else error budget.LimitError {
        try check(error.message == "aggregate.make field type mismatch",
            "static aggregate.make field type");
        return true;
    };
    fail ProbeError { message="incorrect aggregate.make type accepted"; };
}
function rejectWrongArity(engine identity values.Engine,shape aggregate.TypeId)
    returns Bool fails budget.LimitError,ProbeError {
    let wrong be values.make(engine,shape,[])
    else error budget.LimitError {
        try check(error.message == "aggregate.make arity or member capacity mismatch",
            "static aggregate.make arity");
        return true;
    };
    fail ProbeError { message="incorrect aggregate.make arity accepted"; };
}
function rejectForeignValue(engine identity values.Engine,shape aggregate.TypeId,
    foreign values.ValueId)
    returns Bool fails budget.LimitError,ProbeError {
    let wrong be values.make(engine,shape,[foreign])
    else error budget.LimitError {
        try check(error.message == "foreign or invalid U1b aggregate ValueId",
            "foreign U1b aggregate value");
        return true;
    };
    fail ProbeError { message="foreign U1b aggregate value accepted"; };
}
function run() returns Bool fails budget.LimitError,graph_verify.InvalidGraph,ProbeError {
    let root be try budget.developmentRequest();
    let metadataOwner be try budget.metadataOwner(root);
    let metadataPhase be try budget.constructionPhase(metadataOwner);
    let data be try meta.create(metadataOwner,metadataPhase);
    let signature be try meta.signature(data,metadataPhase,[meta.i64()],[meta.i64()]);
    let graph be try aggregate.create(metadataOwner,metadataPhase);
    let i64 be try aggregate.primitive(graph,meta.i64());
    let pred be try aggregate.primitive(graph,meta.pred());
    let oneType be try aggregate.aggregate(graph,metadataPhase,[i64]);
    let emptyType be try aggregate.aggregate(graph,metadataPhase,[]);
""",
    ]
    for n in SIZES:
        statements.append(
            f"    let shape{n} be try aggregate.aggregate(graph,metadataPhase,["
            + ",".join("i64" for _ in range(n))
            + "]);\n"
        )
    statements.extend(
        [
            """    let nestedType be try aggregate.aggregate(graph,metadataPhase,[shape9,i64]);
    try aggregate.freeze(graph);
    let owner be try budget.functionOwner(root,false);
    let phase be try budget.constructionPhase(owner);
    let engine be try values.create(graph,owner,phase);
    let empty be try values.make(engine,emptyType,[]);
    let boolValue be try values.scalar(engine,pred,1);
    let defaultValue be try values.scalar(engine,i64,99);
    let single be try values.make(engine,oneType,[defaultValue]);
    try check(try rejectWrongMake(engine,oneType,boolValue),"wrong make type rejected");
    try check(try rejectWrongArity(engine,oneType),"wrong make arity rejected");
    try check(try rejectWrongField(engine,single),"field out of bounds rejected");
    try check(try rejectWrongSet(engine,single,boolValue),"wrong replacement type rejected");
"""
        ]
    )
    expected = []
    for n in SIZES:
        pieces = []
        original = tuple(11 + i for i in range(n))
        for i in range(n):
            variable = f"v{n}_{i}"
            statements.append(
                f"    let {variable} be try values.scalar(engine,i64,{original[i]});\n"
            )
            pieces.append(variable)
        statements.append(
            f"    let old{n} be try values.make(engine,shape{n},["
            + ",".join(pieces)
            + "]);\n"
        )
        statements.append(
            f"    let replacement{n} be try values.scalar(engine,i64,{1000+n});\n"
        )
        mid = n // 2
        statements.append(
            f"    let changed{n} be try values.set(engine,old{n},{mid},replacement{n});\n"
        )
        for item, field in (
            (f"old{n}", mid),
            (f"changed{n}", mid),
            (f"old{n}", 0),
            (f"changed{n}", 0),
        ):
            statements.append(
                "    output(try values.bits(engine,"
                f"try values.get(engine,{item},{field})));\n"
            )
        after = original[:mid] + (1000 + n,) + original[mid + 1 :]
        expected.extend((original[mid], after[mid], original[0], after[0]))
    statements.append(
        """    let nestedOld be try values.make(engine,nestedType,[old9,defaultValue]);
    let nestedNew be try values.set(engine,nestedOld,0,changed9);
    let nestedBefore be try values.get(engine,nestedOld,0);
    let nestedAfter be try values.get(engine,nestedNew,0);
    output(try values.bits(engine,try values.get(engine,nestedBefore,4)));
    output(try values.bits(engine,try values.get(engine,nestedAfter,4)));
    let siblingOwner be try budget.functionOwner(root,false);
    let siblingPhase be try budget.constructionPhase(siblingOwner);
    let sibling be try values.create(graph,siblingOwner,siblingPhase);
    let foreign be try values.scalar(sibling,i64,7);
    try check(try rejectForeignValue(engine,oneType,foreign),"foreign value rejected");
    try values.close(sibling); try budget.finishPhase(siblingPhase);
    try budget.close(siblingOwner);
    try values.close(engine); try budget.finishPhase(phase);
    try budget.close(owner);
    try aggregate.close(graph); try meta.close(data);
    try budget.finishPhase(metadataPhase); try budget.close(metadataOwner);
    try check(root.live == 0 and root.pending == 0,
        "all opt-in aggregate owner allocations released");
    try budget.close(root);
    output("aggregate-value-copy:ok");
    return true;
}
function main() {
    let okay be run()
    else error budget.LimitError {
        output("limit:"+error.category+":"+error.message);
        process.setExitCode(1); return;
    } else error graph_verify.InvalidGraph {
        output("graph:"+error.message);
        process.setExitCode(1); return;
    } else error ProbeError {
        output("probe:"+error.message);
        process.setExitCode(1); return;
    };
}
main();
"""
    )
    expected.extend((15, 1009))
    return "".join(statements), "".join(f"{x}\n" for x in expected) + "aggregate-value-copy:ok\n"


class U1AggregateValuesTests(unittest.TestCase):
    def test_immutable_make_get_set_against_python_value_copy_oracle(self):
        source_text, expected_output = build_program()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "compiler").symlink_to(ROOT / "src/compiler", target_is_directory=True)
            source = root / "values.eri"
            source.write_text(source_text, encoding="utf-8")
            target = root / "values"
            self.assertEqual(build_native(source, target, root), 0)
            completed = subprocess.run([str(target)], capture_output=True, text=True, timeout=120)
            self.assertEqual(
                (completed.returncode, completed.stdout, completed.stderr),
                (0, expected_output, ""),
            )


if __name__ == "__main__":
    unittest.main()
