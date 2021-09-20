import random
from testflows.core import *

def version(*v):
    """Check ClickHouse version.
    """
    def _check(test):
        return test.context.clickhouse_version in v
    return _check

@TestScenario
@Repeat(10, until="complete") # repeat test 10 times, until can be "pass", "fail" or "complete" 
def test1(self):
    pass

@TestScenario
@Retry(10) # retry test until it pass, any failed tries are not counted
def test2(self):
    assert random.random() < 0.2 # 20% fail rate
  
@TestScenario
@Repeat(2)
@Retry(10)
def test3(self):
    assert random.random() < 0.5 # 50% fail raite

@TestScenario
@Skipped("not supported on 21.8", when=version("21.8"))
def test4(self):
    """This test is skipped if version is 21.8
    The 'when' argument takes a callable that is called
    right before trying to run the body of the test.
    Note that version() returns a function.
    """
    assert False

@TestScenario
def test5(self):
    raise RuntimeError("should not run")

@TestScenario
def test6(self):
    raise RuntimeError("shoult not run")

@TestModule
@FFails({
    "test4": (Skip, "not supported on 21.8", version("21.8")), # FFails overrides Skipped of test4 so we must specify force result again
    "test5": (XFail, "always forcing xfail"), # the body of the test is not executed
    "test6": (XFail, "force xfail on 21.8", version("21.8")) # also supports optional 'when' callable as the last argument 
})
def module(self):
    self.context.clickhouse_version = "21.8"

    for scenario in loads(current_module(), Scenario):
        scenario()

if main():
    module()
