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
        with When(f"for {example}"):
            check_water(**example._asdict())

examples = ExamplesTable(
    header="water_type temperature",
    rows=[
       ("hot", "+60C"),
       ("cold", "-5C"),
    ]
)

@TestFeature
def with_examples(self):
    Scenario("check water types 0", run=check_water_types)
    Scenario("check water types 1", run=check_water_types, examples=examples) 

if main():
    with_examples()
