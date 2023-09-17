#!/usr/bin/env python3
from testflows.core import *
from testflows.asserts import error, values, raises


@TestStep(Given)
def given_with_yield(self, num):
    try:
        yield num
    finally:
        with Finally(f"clean up given with yield {num}"):
            pass


@TestStep(Given)
def open_log(self, name, mode="w+"):
    with open(name, mode) as log:
        yield log


@TestBackground
def open_logs(self):
    with Given("open log1"):
        log1 = open_log(name="helllo")
    with Given("open log2"):
        log2 = open_log(name="helllo2")
    yield log1, log2
    with Finally("I close the logs"):
        pass


@TestBackground
def open_logs_with_fail(self, ref):
    try:
        with Given("open log1"):
            log1 = open_log(name="helllo")
            ref.append(log1)
        with Given("open log that fails"):
            log2 = open_log(name="foozoo", mode="r")
            ref.append(log2)
        with Given("open log2"):
            log3 = open_log(name="helllo2")
            ref.append(log3)
        yield log1, log2, log3
    finally:
        with Finally("I close the logs"):
            pass


@TestBackground
def open_logs_and_given_with_yield(self):
    with Given("given with yield"):
        assert given_with_yield(num=1) == 1, error()
    with Given("open log1"):
        log1 = open_log(name="helllo")
    with Given("open log2"):
        log2 = open_log(name="helllo2")
    yield self


@TestFeature
def background(self):
    """Check using Background test definition
    and TestBackground decorator.
    """
    with Scenario("direct call"):
        with Given("opened logs"):
            log, log2 = open_logs()
        assert log.closed is False and log2.closed is False, error()
    assert log.closed is True and log2.closed is True, error()

    with Scenario("direct call inside test definition"):
        with Background("open logs"):  # works
            log, log2 = open_logs()
        assert log.closed is False and log2.closed is False, error()
    assert log.closed is True and log2.closed is True, error()

    with Scenario("open logs with fail"):
        logs = []
        with Check("proper background cleanup"):
            with raises(Error):
                Background(test=open_logs_with_fail)(ref=logs)

    with Scenario("background with given with yield"):
        with Background("my background"):
            open_logs_and_given_with_yield()


@TestStep(Given)
def given_with_multiple_yields(self):
    try:
        note("first")
        yield 1
        note("second")
        yield 2
    finally:
        note("third")
        yield 3


@TestScenario
def check_given_with_multiple_yields(self):
    with Given("setup"):
        assert given_with_multiple_yields() == 1, error()


@TestFeature
def feature(self):
    Scenario(run=check_given_with_multiple_yields)
    background()


if main():
    feature()
