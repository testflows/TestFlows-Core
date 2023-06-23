#!/usr/bin/python3
from testflows.core import *
from testflows.asserts import error
from testflows._core.objects import Result


@TestSuite
def my_suite(self):
    with Scenario("my inner test"):
        fail("failed")


@TestScenario
def my_test(self):
    ok("success")


@TestOutline
def check_result(self, test, flags=None):
    with Check("running the test"):
        r = Scenario(test=test, flags=Flags(flags))()

    with Then("the result object should be returned"):
        assert isinstance(r, Result), error("not a result object")

    with And("start_time should be set"):
        assert r.start_time is not None, error("start_time should not be None")

    with And("test_time should be set"):
        assert r.test_time is not None, error("test_time should not be None")


@TestFeature
def feature(self):
    """Check returned result objects."""
    with Example("scenario result object"):
        check_result(test=my_test)

    with Example("suite result object"):
        check_result(test=my_suite, flags=XFAIL)


if main():
    feature()
