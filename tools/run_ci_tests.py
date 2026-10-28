#!/usr/bin/env python3
"""Run the ordinary suite and retain machine-readable outcomes, including skips."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import platform
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

class Result(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.passed=0
    def addSuccess(self,test):
        super().addSuccess(test)
        self.passed+=1

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    discovered=suite.countTestCases();started=time.monotonic()
    result=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(suite)
    report={'status':'success' if result.wasSuccessful() else 'failed','discovered_tests':discovered,
            'tests_run':result.testsRun,'passed':result.passed,
            'unsuccessful_tests':result.testsRun-result.passed-len(result.skipped)-len(result.expectedFailures),
            'failure_records':len(result.failures),
            'skipped':[{'test':test.id(),'reason':reason} for test,reason in result.skipped],
            'failures':[{'test':test.id(),'traceback':trace} for test,trace in result.failures],
            'errors':[{'test':test.id(),'traceback':trace} for test,trace in result.errors],
            'expected_failures':[test.id() for test,_ in result.expectedFailures],
            'unexpected_successes':[test.id() for test in result.unexpectedSuccesses],
            'seconds':time.monotonic()-started,'platform':platform.platform(),
            'python':platform.python_version(),'cc':os.environ.get('CC')}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return 0 if result.wasSuccessful() else 1

if __name__=='__main__':raise SystemExit(main())
