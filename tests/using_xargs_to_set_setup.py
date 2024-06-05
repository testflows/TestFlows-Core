from testflows.core import *


@TestStep(Given)
def do_something(self):
    yield
    note("doing somthing as a setup - cleanup")


@TestScenario
def test1(self):
    note("hello from test1")


@TestScenario
def test2(self):
    note("hello from test2")


@TestFeature
@XArgs({"/feature/test:": ({"setup": do_something},)})
def feature(self):
    with Given("my feature setup"):
        note("I do my feature setup")

    with When("my feature action"):
        note("I do my feature action")

    for scenario in loads(current_module(), Scenario):
        scenario()


if main():
    feature()
