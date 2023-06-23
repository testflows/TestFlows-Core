#!/usr/bin/env python3
from testflows.core import *


@TestScenario
def check_water(self, water_type, temperature):
    with When(f"I open {water_type}"):
        with Then(f"water temperature should be {temperature}"):
            pass


@TestOutline(Scenario)
@Examples(
    header="water_type temperature",
    rows=[
        ("hot", "+30C"),
        ("cold", "5C"),
    ],
)
def check_water_types(self, water_type, temperature):
    """Check water types."""
    with When(f"for example {water_type}, {temperature}"):
        check_water(water_type=water_type, temperature=temperature)


@TestOutline(Test)
@Name("checking water type outline")
@Examples(
    "water_type temperature",
    [
        (
            "hot",
            "+30C",
            args(
                name="checking water {water_type} with {temperature}",
                requirements=[],
                flags=TE,
            ),
        ),
        ("cold", "5C"),
    ],
)
def check_water_type_outline(self, water_type, temperature):
    check_water(water_type=water_type, temperature=temperature)


@TestScenario
@Examples(
    header="water_type temperature",
    rows=[
        ("hot", "+33C"),
        ("cold", "10C"),
    ],
)
def check_more_water_types(self):
    for example in self.examples:
        Example(name=example, test=check_water)(**vars(example))


examples = Examples(
    header="water_type temperature",
    rows=[
        ("hot", "+60C", args(requirements=[], flags=TE)),
        ("cold", "-5C"),
    ],
)


@TestOutline(Suite)
@Examples(header="name", rows=[("v",), ("n",)])
def suite_outline(self, name):
    note(f"hello {name}")
    Scenario(run=check_water_types)


@TestOutline(Step)
@Examples(header="name", rows=[("v",), ("n",)])
def step_outline(self, name):
    note(f"hello {name}")


@TestOutline(Feature)
@Examples(
    header="name lastname",
    rows=[
        (
            "v",
            "z",
        ),
        (
            "n",
            "l",
        ),
    ],
)
def with_examples(self, name, lastname=None):
    for example in examples:
        note([example, example._args])
    step_outline()
    with When("step outline", test=step_outline):
        step_outline(name="hello")
    Suite(test=suite_outline)(name="hello")
    check_more_water_types()
    Scenario("check water types 0", run=check_water_types)
    Scenario("check water types 1", run=check_water_types, examples=examples)
    Scenario("check more water types 0", run=check_more_water_types)
    Scenario("check more water types 1", run=check_more_water_types, examples=examples)
    Scenario("check water types outline 0", run=check_water_type_outline)
    Scenario("check water types outline 1", test=check_water_type_outline)()
    Scenario("check water types outline 2", test=check_water_type_outline)(
        water_type="cold", temperature="5C"
    )
    check_water_type_outline()
    check_water_type_outline(water_type="cold", temperature="5C")
    with Scenario("my water types", examples=examples) as test:
        check_water_type_outline(**vars(test.examples[0]))
        check_water_type_outline(water_type="cold", temperature="5C")


if main():
    with_examples()
