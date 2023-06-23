import random
from testflows.core import *


def version(*v):
    """Check ClickHouse version."""

    def _check(test):
        return test.context.clickhouse_version in v

    return _check


@TestScenario
@Repeat(
    10, until="complete"
)  # repeat test 10 times, until can be "pass", "fail" or "complete"
def test1(self):
    pass


@TestScenario
@Retry(10)  # retry test until it pass, any failed tries are not counted
def test2(self, fail_rate=0.2):
    assert random.random() < fail_rate  # 20% fail rate


@TestScenario
@Repeat(2)
@Retry(10)
def test3(self):
    assert random.random() < 0.5  # 50% fail raite


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


@TestScenario
def test7(self):
    with Step("could fail", repeats={"": (10, "complete")}, flags=EERROR):
        assert random.random() < 0.3  # 70% fail rate


@TestScenario
def test8(self, fail_rate=0.2):
    assert random.random() < fail_rate  # provide fail rate


@TestScenario
@Repeat(4)
@Retry(4)
def nested_retries(self):
    """Check handling of nested retries."""
    for attempt in retries(count=10):
        with attempt:
            Scenario(test=test2, retries=Retry(count=1))()


@TestScenario
@Repeat(4)
@Retry(4, initial_delay=5)
def nested_retries_with_initial_delay(self):
    """Check handling of nested retries with initial delay."""
    for attempt in retries(count=10, initial_delay=1):
        with attempt:
            Scenario(test=test2, retries=Retry(count=1))()


@TestScenario
def repeats_object(self):
    """Check repeats object."""
    with Check("until complete", flags=XFAIL):
        for iteration in repeats(count=10, until="complete"):
            with iteration:
                Scenario(test=test8)(fail_rate=0.5)

    with Check("until pass", flags=XFAIL):
        for iteration in repeats(count=10, until="pass"):
            with iteration:
                Scenario(test=test8)(fail_rate=0.5)

    with Check("until fail", flags=XFAIL):
        for iteration in repeats(count=10, until="fail"):
            with iteration:
                Scenario(test=test8)(fail_rate=0.5)

    with Check("repeat function"):

        def add_note(m):
            note(str(m))
            return m

        note(repeat(add_note, count=2)("hello"))


@TestModule
@FFails(
    {
        "test4": (
            Skip,
            "not supported on 21.8",
            version("21.8"),
        ),  # FFails overrides Skipped of test4 so we must specify force result again
        "test5": (
            XFail,
            "always forcing xfail",
        ),  # the body of the test is not executed
        "test6": (
            XFail,
            "force xfail on 21.8",
            version("21.8"),
        ),  # also supports optional 'when' callable as the last argument
    }
)
def module(self):
    self.context.clickhouse_version = "21.8"

    for scenario in loads(current_module(), Scenario):
        scenario()


if main():
    module()
