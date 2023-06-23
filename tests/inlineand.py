from testflows.core import *
from testflows.asserts import error, raises

from testflows._core.testtype import TestType, TestSubType


@TestOutline(Scenario)
@Examples(
    "sibling",
    [
        (When,),
        (Given,),
        (Finally,),
        (But,),
        (By,),
        (Then,),
    ],
    args=Name("check {sibling.subtype!s} subtype inherirance"),
)
def check_subtype_inheritance(self, sibling):
    """Check that And step properly inherits the subtype
    of its sibling.
    """
    with sibling(f"I have a sibling of a {str(sibling.subtype)} subtype"):
        pass

    with And("I have And step that follows it") as step:
        with Then("its type must be a Step"):
            assert step.type is TestType.Step

        with Then(f"its subtype must be {str(sibling.subtype)}"):
            assert step.subtype is sibling.subtype

    with And("I have another And step that follows it") as step:
        with Then("its type must be a Step"):
            assert step.type is TestType.Step

        with Then(f"its subtype must be {str(sibling.subtype)}"):
            assert step.subtype is sibling.subtype


@TestOutline(Scenario)
@Examples(
    "sibling",
    [(Test,), (Scenario,), (When,), (Given,)],
    args=Name("check {sibling.__name__!s} sibling type"),
)
def check_when_sibling_is_of_invalid_type(self, sibling):
    """Check that a exception is raised when sibling
    has an invalid type.
    """
    with sibling(f"sibling of a {sibling.__name__} type"):
        with raises(TypeError):
            with And("I have And step that follows it"):
                pass


@TestFeature
@Name("inline And")
def feature(self):
    """Check when inline And is defined
    it can properly inherit subtype of its sibling
    if it has the same type as the sibling.
    """
    Scenario(run=check_subtype_inheritance)
    Scenario(run=check_when_sibling_is_of_invalid_type)


if main():
    feature()
