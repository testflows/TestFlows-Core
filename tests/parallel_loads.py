import time
from testflows.core import *


@TestScenario
def test1(self):
    time.sleep(1)
    note("test1")


@TestScenario
def test2(self):
    time.sleep(1)
    note("test2")


@TestScenario
@Flags(NO_PARALLEL)
def test3(self):
    time.sleep(1)
    note("test3")


@TestScenario
def test4(self):
    time.sleep(1)
    note("test4")


@TestScenario
def test5(self):
    time.sleep(1)
    note("test5")


@TestScenario
@Flags(NO_PARALLEL)
def test6(self):
    time.sleep(1)
    note("test6")


@TestScenario
@Flags(NO_PARALLEL)
def test7(self):
    time.sleep(1)
    note("test7")


@TestScenario
def test8(self):
    time.sleep(1)
    note("test8")


@TestScenario
def test9(self):
    time.sleep(1)
    note("test9")


@TestFeature
def feature(self):
    with Pool(3) as pool:
        for scenario in loads(current_module(), Scenario):
            flags = getattr(scenario, "flags", Flags())
            if flags & NO_PARALLEL:
                join()
            else:
                flags |= PARALLEL
            Scenario(run=scenario, flags=flags, executor=pool)
        join()


feature()
