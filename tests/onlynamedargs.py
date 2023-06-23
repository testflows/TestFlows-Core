from testflows.core import *
from testflows.asserts import raises, error


@TestStep
def step(self, arg1, arg2=None):
    pass


@TestCase
def case(self, arg1, arg2=None):
    pass


@TestSuite
def suite(self, arg1, arg2=None):
    pass


@TestBackground
def background(self, arg1, arg2=None):
    pass


@TestOutline
def outline(self, arg1, arg2=None):
    pass


@TestOutline(Scenario)
@Examples(
    "test",
    [(step,), (case,), (outline,), (background,)],
    args=Name("test={test.type.type!s}"),
)
def call_directly(self, test):
    with When("I call a test directly"):
        with raises(TypeError) as exc:
            test(1)

    with Then("I expect TypeError to be raised"):
        assert (
            str(exc.exception)
            == "only named arguments are allowed but (1,) positional arguments were passed"
        ), error()


@TestOutline(Scenario)
@Examples(
    "outer_test test",
    [
        (Step, step),
        (When, step),
        (Given, step),
        (But, step),
        (Finally, step),
        (And, step),
        (Scenario, case),
        (Test, case),
        (Background, background),
        (Outline, outline),
        (Test, outline),
        (Scenario, outline),
    ],
    args=Name("outer_test={outer_test.type!s}, test={test.type.type!s}"),
)
def call_using_another_test(self, outer_test, test):
    with When("I call test using another test"):
        with raises(TypeError) as exc:
            outer_test(test=test)(1)

    with Then("I expect TypeError to be raised"):
        assert (
            str(exc.exception)
            == "only named arguments are allowed but (1,) positional arguments were passed"
        ), error()


@TestFeature
@Name("only named arguments")
def feature(self):
    """Check that calling a test takes only named arguments."""
    Scenario(run=call_directly)
    Scenario(run=call_using_another_test)


if main():
    feature()
