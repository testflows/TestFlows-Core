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


@TestBackground
def open_logs(self):
    with Given("open log1"):
        self.append(open("helllo", "w+"))
    with Given("open log2"):
        self.append(open("helllo2", "w+"))
    yield self
    with Finally("I close the logs"):
        pass


@TestBackground
def open_logs_with_fail(self, ref):
    ref.append(self.contexts)
    try:
        with Given("open log1"):
            self.append(open("helllo", "w+"))
        with Given("open log that fails"):
            self.append(open("foozoo", "r"))
        with Given("open log2"):
            self.append(open("helllo2", "w+"))
        yield self
    finally:
        with Finally("I close the logs"):
            for log in self.contexts:
                assert log.closed is False, error()


@TestBackground
def open_logs_and_given_with_yield(self):
    with Given("given with yield"):
        assert given_with_yield(num=1) == 1, error()
    with Given("open log1"):
        self.append(open("helllo", "w+"))
    with Given("open log2"):
        self.append(open("helllo2", "w+"))
    yield self


@TestFeature
def background(self):
    """Check using Background test definition
    and TestBackground decorator.
    """
    with Scenario("direct call"):
        log, log2 = open_logs()
        assert log.closed is False and log2.closed is False, error()
    assert log.closed is True and log2.closed is True, error()

    with Scenario("run test definition"):
        log, log2 = Background(run=open_logs)
        assert log.closed is False and log2.closed is False, error()
    assert log.closed is True and log2.closed is True, error()

    with Scenario("direct call inside test definition"):
        with Background("open logs"):  # works
            log, log2 = open_logs()
        assert log.closed is False and log2.closed is False, error()
    assert log.closed is True and log2.closed is True, error()

    with Scenario("call test definition"):
        log, log2 = Background(test=open_logs)()
        assert log.closed is False and log2.closed is False, error()
    assert log.closed is True and log2.closed is True, error()

    with Scenario("open logs with fail"):
        logs = []
        with Check("proper background cleanup"):
            with raises(Error):
                Background(test=open_logs_with_fail)(ref=logs)
        for log in logs[0]:
            assert log.closed is True, error()

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
