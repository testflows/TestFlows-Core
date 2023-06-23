from testflows.core import *


@TestOutline(Module)
@Examples("name", [("hello",)])
def module_outline(self, name):
    note(name)


@TestOutline
def test_outline(self):
    note("outline")


@TestScenario
def scenario_using_outline(self):
    Example(run=test_outline)


@TestOutline(Scenario)
def scenario_outline(self):
    note("scenario outline")


@TestScenario
def scenario_using_scenario_outline(self):
    scenario_outline()


@TestScenario
def scenario_using_scenario_outline_for_example(self):
    Example(run=scenario_outline)


@TestScenario
@Examples("name value", [("hi", "now"), ("bye", "then")])
def scenario_with_examples(self):
    for example in self.examples:
        note(example)


@TestOutline
def outline_with_args(self, name, value=None):
    note(f"{name} {value}")


@TestOutline(Scenario)
def scenario_outline_with_args(self, name, value=None):
    note(f"{name} {value}")


@TestOutline(Suite)
def suite_outline_with_args(self, name, value=None):
    note(f"{name} {value}")


@TestScenario
@Examples("name value", [("hi", "now"), ("bye", "then")])
def scenario_with_examples_using_outline_with_args(self):
    note(f"scenario with examples using outline with args: {self.examples}")
    for example in self.examples:
        Example(name=example, test=scenario_outline_with_args, type=self.type)(
            **vars(example)
        )
        break


@TestScenario
def scenario_with_inner_examples(self):
    if not self.examples:
        self.examples = Examples("name value", [("hi", "there"), ("bye", "here")])
    for example in self.examples:
        Example(name=example, test=scenario_outline_with_args, type=self.type)(
            **vars(example)
        )


@TestScenario
def scenario(self):
    note(f"{self} scenario")


@TestOutline(Scenario)
@Examples("name value", [("hi", "there"), ("bye", "here")])
def scenario_outline_with_examples_and_args(self, name, value=None):
    note(f"{self} {name} {value}")
    Scenario("my inner scenario", run=scenario_with_examples_using_outline_with_args)


with Module("regression"):
    with Outline("my outline"):
        note("hello")
    module_outline(name="hello")
    test_outline()
    scenario_using_outline()
    scenario_outline()
    scenario_using_scenario_outline()
    scenario_using_scenario_outline_for_example()
    scenario_with_examples()
    outline_with_args(name="hello")
    scenario_outline_with_args(name="hello")
    scenario_with_examples_using_outline_with_args()
    # override built-in examples of the outline
    Scenario(
        run=scenario_with_examples_using_outline_with_args,
        examples=Examples("name value", [("hi", "there")]),
    )
    scenario_with_inner_examples()
    scenario_outline_with_examples_and_args()
    scenario_outline_with_examples_and_args(name="hello", value="there")
    Scenario("my scenario", test=scenario_outline_with_examples_and_args)(
        name="hello", value="there"
    )
    Scenario(
        "my scenario", test=scenario_outline_with_examples_and_args, examples=None
    )(name="hello", value="there")
    Scenario("my scenario", test=scenario_outline_with_examples_and_args)()
    Scenario(
        "run scenario outline that has examples and args",
        run=scenario_outline_with_examples_and_args,
    )
    Scenario(
        "run scenario outline that has examples and args and specify one arg",
        run=scenario_outline_with_examples_and_args,
        args={"name": "hello"},
    )
    Scenario(
        "test scenario outline that has examples and specify test and call args",
        test=scenario_outline_with_examples_and_args,
        args={"name": "hello"},
    )(value="there")

    with Scenario("scenario that calls outline inside"):
        outline = scenario_outline_with_examples_and_args
        outline(**vars(outline.examples[0]))
        Scenario("scenario that runs outline", run=outline)
        Scenario("scenario that is called to run outline", test=outline)()

    # manually run examples
    with Scenario(name="manual examples", test=outline) as test:
        for example in outline.examples:
            Example(name=example, test=outline)(**vars(example))
