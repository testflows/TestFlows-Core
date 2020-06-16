#!/usr/bin/env python3
from testflows.core import *

@TestScenario
def check_water(self, water_type, temperature):
    with When(f"I open {water_type}"):
        with Then(f"water temperature should be {temperature}"):
            pass

@TestScenario
@Examples(
    header="water_type temperature",
    rows=[
       ("hot", "+30C"),
       ("cold", "5C"),
    ]
)
def check_water_types(self):
    """Check water types.
    """
    for example in self.examples:
        with When(f"for example {example}"):
            check_water(**example._asdict())

@TestCase
@Outline
@Examples(
    header="water_type temperature",
    rows=[
       ("hot", "+30C"),
       ("cold", "5C"),
    ]
)
def check_water_type_outline(self, water_type, temperature):
    check_water(water_type=water_type, temperature=temperature)

@TestScenario
@Outline
@Examples(
    header="water_type temperature",
    rows=[
       ("hot", "+30C"),
       ("cold", "5C"),
    ]
)
def check_water_type_outline(self, water_type, temperature):
    check_water(water_type=water_type, temperature=temperature)

@TestScenario
@Examples(
    header="water_type temperature",
    rows=[
       ("hot", "+33C"),
       ("cold", "10C"),
    ]
)
def check_more_water_types(self):
    for example in self.examples:
        Example(name=example, test=check_water)(**vars(example))

examples = ExamplesTable(
    header="water_type temperature",
    rows=[
       ("hot", "+60C"),
       ("cold", "-5C"),
    ]
)

@TestSuite
@Outline
@Examples(
    header="name",
    rows = [
        ("vitaliy",),
        ("natalia",)
    ]
)
def suite_outline(self, name):
    note(f"hello {name}")
    Scenario("check water types 0", run=check_water_types)

@TestStep
@Outline
@Examples(
    header="name",
    rows = [
        ("vitaliy",),
        ("natalia",)
    ]
)
def step_outline(self, name):
    note(f"hello {name}")

@TestFeature
#@Outline
@Examples(
    header="name",
    rows = [
        ("vitaliy",),
        ("natalia",)
    ]
)
def with_examples(self, name=None):
    with When(test=step_outline):
        step_outline()
    Suite(test=suite_outline)()
    Scenario("check water types 0", run=check_water_types)
    Scenario("check water types 1", run=check_water_types, examples=examples) 
    Scenario("check more water types 0", run=check_more_water_types)
    Scenario("check more water types 1", run=check_more_water_types, examples=examples)
    Scenario("check water types outline 0", run=check_water_type_outline)
    Scenario("check water types outline 1", test=check_water_type_outline)()
    Scenario("check water types outline 2", test=check_water_type_outline)(water_type='cold', temperature='5C')
    check_water_type_outline()
    check_water_type_outline(water_type='cold', temperature='5C')
    with Scenario("my water types", examples=examples):
        check_water_type_outline()
        check_water_type_outline(water_type='cold', temperature='5C')

if main():
    with_examples()
