from testflows.core import *
from testflows.asserts import error


@TestScenario
@Tags("tag2")
def test1(self):
    note("test1")


@TestScenario
@Flags(TE | UT)
@Attributes(("attr1", "value1"))
@Tags("tag1", "tag2")
def test2(self):
    note("test2")


@TestScenario
@Flags(UT)
@Attributes(("name", "value"))
def test3(self):
    note("test3")


@TestScenario
@Requirements(Requirement("RQ.SRS001.Name", "1.0"))
@Name("custom name")
def test4(self):
    note("test 4")


@TestModule
@Name("scenario filtering")
def regression(self):
    with Suite("by tag"):
        with Scenario("name & ~name"):
            scenarios = loads(
                current_module(), Scenario, filter=has.tag("tag2") & ~has.tag("tag1")
            )
            test_list = [scenario for scenario in scenarios]
            assert test_list == [test1], error()

    with Suite("by attribute"):
        with Scenario("name & value"):
            scenarios = loads(
                current_module(),
                Scenario,
                filter=has.attribute.name("name") & has.attribute.value("value"),
            )
            test_list = [scenario for scenario in scenarios]
            assert test_list == [test3], error()

        with Scenario("name"):
            scenarios = loads(
                current_module(), Scenario, filter=has.attribute.name("attr1")
            )
            test_list = [scenario for scenario in scenarios]
            assert test_list == [test2], error()

    with Suite("by requirement"):
        with Scenario("version"):
            scenarios = loads(
                current_module(), Scenario, filter=has.requirement.version("1.0")
            )
            test_list = [scenario for scenario in scenarios]
            assert test_list == [test4], error()

        with Scenario("name"):
            scenarios = loads(
                current_module(),
                Scenario,
                filter=has.requirement.name.startingwith("RQ.SRS001"),
            )
            test_list = [scenario for scenario in scenarios]
            assert test_list == [test4], error()

    with Suite("by flag"):
        with Scenario("flag"):
            scenarios = loads(current_module(), Scenario, filter=has.flag(UT))
            test_list = [scenario for scenario in scenarios]
            assert test_list == [test2, test3], error()

        with Scenario("flag & ~flag"):
            scenarios = loads(
                current_module(), Scenario, filter=has.flag(UT) & ~has.flag(TE)
            )
            test_list = [scenario for scenario in scenarios]
            assert test_list == [test3], error()

    with Suite("by name"):
        with Scenario("name.startingwith"):
            scenarios = loads(
                current_module(), Scenario, filter=has.name.startingwith("test")
            )
            test_list = [scenario for scenario in scenarios]
            assert test_list == [test1, test2, test3], error()

        with Scenario("name.containing"):
            scenarios = loads(
                current_module(), Scenario, filter=has.name.containing("2")
            )
            test_list = [scenario for scenario in scenarios]
            assert test_list == [test2], error()

        with Scenario("name.endingwith"):
            scenarios = loads(
                current_module(), Scenario, filter=has.name.endingwith("3")
            )
            test_list = [scenario for scenario in scenarios]
            assert test_list == [test3], error()

        with Scenario("custom name"):
            scenarios = loads(
                current_module(), Scenario, filter=has.name.containing("custom")
            )
            test_list = [scenario for scenario in scenarios]
            assert test_list == [test4], error()


if main():
    regression()
