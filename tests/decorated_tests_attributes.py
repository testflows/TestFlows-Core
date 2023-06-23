#!/usr/bin/python3
from testflows.core import *
from testflows.asserts import error
from testflows._core.testtype import TestSubType


@TestScenario
def test1_implicit_name(self):
    pass


@TestScenario
@Name("test2")
def test2_explicit_name(self):
    pass


@TestScenario
@Tags("tag1", "tag2")
def test3_with_tags(self):
    pass


@TestScenario
@Args(tags=("tag1", "tag2"))
def test3_with_tags_using_args(self):
    pass


@TestScenario
def test4_with_description_using_docstring(self):
    """test4 description"""
    pass


@TestScenario
@Description("test5 description")
def test5_with_description(self):
    pass


@TestScenario
@Flags(TE)
def test6_with_flags(self):
    pass


@TestScenario
@Args(flags=Flags(TE))
def test7_with_flags_using_args(self):
    pass


@TestScenario
@Args(args={"arg0": "value0"})
def test8_with_args_set_using_args(self, arg0="foo"):
    pass


@TestStep(When)
def step1(self):
    pass


@TestStep
@Args(subtype=TestSubType.When)
def step2_subtype_set_using_args(self):
    pass


@TestFeature
@Name("decorated test attributes")
def feature(self):
    with Scenario("check accessing name attribute when test has implicit name"):
        assert test1_implicit_name.name == "test1 implicit name", error()

    with Scenario("check accessing name attribute when test uses @Name"):
        assert test2_explicit_name.name == "test2", error()

    with Scenario("check accessing tags attribute when test uses @Tags"):
        assert tuple(test3_with_tags.tags) == ("tag1", "tag2"), error()

    with Scenario("check accessing tags attribute when test uses @Args to set tags"):
        assert tuple(test3_with_tags_using_args.tags) == ("tag1", "tag2"), error()

    with Scenario("check accessing type attribute"):
        assert test1_implicit_name.type is Scenario, error()

    with Scenario("check accessing description attribute when test uses doc string"):
        assert (
            test4_with_description_using_docstring.description == "test4 description"
        ), error()

    with Scenario("check accessing description attribute when test uses @Description"):
        assert test5_with_description.description == "test5 description", error()

    with Scenario("check accessing flags attribute when test uses @Flags"):
        assert str(test6_with_flags.flags) == "TE", error()

    with Scenario("check accessing flags attribute when test uses @Args to set flags"):
        assert str(test7_with_flags_using_args.flags) == "TE", error()

    with Scenario("check accessing args attribute when test using @Args to set args"):
        assert test8_with_args_set_using_args.args == {"arg0": "value0"}, error()

    with Scenario("check subtype attribute for a step"):
        assert step1.subtype is TestSubType.When, error()

    with Scenario("check subtype attribute for a step that has subtype using @Args"):
        assert step2_subtype_set_using_args.subtype is TestSubType.When, error()


if main():
    feature()
