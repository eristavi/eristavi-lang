"""Cheap regression subset; the 150-case scale study remains explicit opt-in."""
import unittest

from tools.probes.u2_resource_baseline import measure


class U2ResourceBaselineTests(unittest.TestCase):
    def test_existing_stage0_and_native_match_cleanup_failure_oracle(self):
        result = measure((2,), 'cc', ('-O2',))
        record, = result['measurements']
        self.assertEqual(len(record['cases']), 14)
        for case in record['cases']:
            self.assertEqual(case['stage0'], case['expected'])
            self.assertEqual(case['native'], case['expected'])


if __name__ == '__main__': unittest.main()
