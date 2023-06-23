#!/usr/bin/python3
from testflows.core import *


@TestStep
def simple_step(self, name=None):
    note(f"simple step {name}")


@TestStep(When)
@Name("I do something")
def do_something(self, action=None):
    note(f"do something {action}")


@TestCase
@Name("My test case")
def test(self):
    pass


@TestCase
@Name("My test case")
def test(self):
    pass


@TestStep(When)
@Name("I do something")
def do_something(self, action=None):
    note(f"do something {action}")


@TestStep
@Name("I do something")
def do_something(self, action=None):
    note(f"do something {action}")


@TestStep(Given)
@Name("I have some resource")
def open_resource(self, name=None):
    try:
        note("I open resource")
        yield
    finally:
        note("I close resource")


@TestScenario
@Name("{$cls.name} my custom test")
@Args(format_name=True)
def custom_test(self, name=None):
    note(f"custom test {name}")


@TestScenario
@Name("simple test")
def simple_test(self, name=None):
    note(f"simple test {name}")


@TestScenario
@Name("test with inline steps")
def inline_steps(self):
    with Step("inline step 0"):
        pass

    with Step("inline step 1"):
        pass


@TestScenario
@Name("test with inline scenarios")
def inline_tests(self):
    with Scenario("inline scenario 0"):
        pass

    with Scenario("inline scenario 1"):
        pass


@TestStep
def my_step_with_arg(self, name):
    note(f"my name is {name}")


@TestFeature
@Name("test definitions")
def feature(self):
    my_step_with_arg(name="hello")
    Scenario(run=Scenario("my inner scenario", test=simple_test))
    Scenario(test=Scenario("my inner scenario 2", test=simple_test))()
    with Scenario("run simple test by calling scenario directly"):
        simple_test(name="name0")
    with Scenario(
        "run simple test by defining scenario over the test and calling it directly"
    ):
        Scenario(test=simple_test, flags=TE)(name="name1")
    with Scenario("run simple test using short run form"):
        Scenario(run=simple_test, flags=TE)
    with Scenario("{$cls.name} {name} 1", test=custom_test):
        custom_test(name="hello")

    simple_step()
    custom_test()
    simple_step(name="hello there")
    When(test=simple_step)()
    When("I run simple step", run=simple_step, args={"name": "hello"})
    When(run=simple_step)
    Given("I {$cls.name} open resource {name}", test=open_resource, format_name=True)(
        name="hello"
    )

    with Given("I {$cls.name} open resource", test=open_resource, format_name=True):
        note("adding to beggining of test")
        open_resource()
        note("adding to the end of test")


if main():
    feature()
