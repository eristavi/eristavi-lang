"""Cheap accounting checks: no compiler build or native profile execution."""
import json
import struct
import unittest

from test_u1b_runtime_hotspot import FIELDS, PHASES, SOURCE_COUNTERS, decode, observed_application


def record(tag, clock, counter):
    return struct.pack("<" + "Q" * len(FIELDS), tag, clock,
                       *[counter * (i + 1) for i in range(len(FIELDS) - 3)],
                       0)  # live_graphs is a gauge, not an additive counter.


class U1BProfileDecoderTests(unittest.TestCase):
    def test_compiler_trace_maps_source_symbols_and_entry(self):
        subjects = ["entry"] + [f"f{i} {name}$10$11" for i, name in enumerate(SOURCE_COUNTERS)]
        diagnostics = "\n".join("[erist-phase] " + json.dumps({
            "event": "begin", "phase": "universal-lower-function", "subject": subject,
        }) for subject in subjects)
        original = "\n" + "".join(f"f{i}:\n    ret\n" for i in range(len(SOURCE_COUNTERS)))
        instrumented, symbols = observed_application(original, diagnostics)
        self.assertEqual(symbols.keys(), SOURCE_COUNTERS.keys())
        self.assertEqual(instrumented.count("pushfq"), len(SOURCE_COUNTERS))
        self.assertEqual(instrumented.count("popfq"), len(SOURCE_COUNTERS))

    def test_raw_units_reconcile_across_repeated_phases(self):
        raw = b"".join((record(21, 100, 10), record(22, 150, 30),
                        record(21, 250, 35), record(0, 500, 60)))
        rows, stages = decode(raw)
        for field in FIELDS[2:-1]:
            self.assertEqual(sum(stage[field] for stage in stages.values()),
                             rows[-1][field] - rows[0][field])
        self.assertEqual(stages[PHASES[21]]["intervals"], 2)
        for stage in stages.values():
            self.assertEqual(stage["gc_seconds_inclusive"], stage["gc_time_ns"] / 1e9)
            self.assertEqual(stage["wall_seconds"], stage["wall_ns"] / 1e9)

    def test_rejects_incomplete_unknown_and_nonmonotonic_records(self):
        for raw in (b"", b"x", record(0, 1, 0),
                    record(99, 1, 0) + record(0, 2, 1),
                    record(0, 2, 0) + record(0, 1, 1),
                    record(0, 1, 2) + record(0, 2, 1)):
            with self.subTest(bytes=len(raw)), self.assertRaises(AssertionError):
                decode(raw)
