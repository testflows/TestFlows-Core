#!/usr/bin/env python3
import time
from testflows.core import *

pool = Pool(3)


@TestScenario
def subtest(self):
    with Step("step"):
        time.sleep(1)


@TestScenario
def test1(self):
    with Step("step"):
        note(f"{self.name} note1")
    pool.submit(Scenario(test=subtest)).result()

    # if self.name.endswith("test1"):
    #    fail(f"{self.name} failed")


@TestScenario
@Parallel(True)
@Executor(pool)
def ptest(self):
    note("parallel test")
    time.sleep(1)
    note("parallel test done")
    fail(f"{self.name} failed")


@TestScenario
def ptest2(self):
    note("parallel test")
    try:
        try:
            for i in range(10):
                with Step("step"):
                    time.sleep(0.1)
        finally:
            note("tryin to cleanup")
            with Given("I try to do some setup"):
                pass
    finally:
        with Finally("clean up"):
            note(f"{self.name} clean up")
    note("parallel test done")


@TestScenario
def ptest3(self):
    fail("failed")


@TestSuite
def suite(self):
    self.executor = Pool(3)

    tasks = []
    with pool:
        for i in range(3):
            tasks.append(Scenario(name=f"ptest2-{i}", run=ptest2, parallel=True))
            tasks.append(Scenario(run=ptest3, parallel=True))

        join(*tasks)


if main():
    suite()
