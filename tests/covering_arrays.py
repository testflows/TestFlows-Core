from testflows.core import *
from testflows.combinatorics import CoveringArray, product


@TestPattern(Scenario)
def homogeneous(self):
    """Check different configurations of covering arrays for homogeneous values
    where each parameter has the same number of values.
    """
    with Given("I choose values for each parameter"):
        values = choose("values", list(range(either(1, 2, 3))))

    with And("I choose number of parameters"):
        number_of_parameters = choose("number of parameters", either(1, 2, 3, 4, 5, 6))

    with And("I create corresponding parameters dictionary"):
        parameters = {}
        for i in range(number_of_parameters):
            parameters[i] = values
        parameters = define("parameters", parameters)

    with And("I choose covering strength"):
        strength = choose("strength", either(1, 2, 3, 4, 5))

    with When(
        "I create covering array",
        description=f"t={strength},k={number_of_parameters},v={len(values)}",
    ):
        covering_array = CoveringArray(parameters=parameters, strength=strength)
        note(str(covering_array))

    with Then("it should cover all t-way combinations"):
        covering_array.check()


@TestPattern(Scenario)
def heterogeneous(self):
    """Check different configurations of covering arrays with heterogeneous values
    where each parameter has different number of values.
    """
    with Given("I choose number of parameters"):
        number_of_parameters = choose("number of parameters", either(2, 3, 4))

    with And("I choose different number of values for each parameter"):
        values = []
        value_combinations = list(
            filter(
                lambda l: len(set(l)) != 1, product(*[[1, 2, 3]] * number_of_parameters)
            )
        )
        value_counts = either(*value_combinations)

        for i, value_count in enumerate(value_counts):
            values.append(list(range(value_count)))

        values = choose("values", values)

    with And("I create corresponding parameters dictionary"):
        parameters = {}
        for i in range(number_of_parameters):
            parameters[i] = values[i]
        parameters = define("parameters", parameters)

    with And("I choose covering strength"):
        strength = choose("strength", either(1, 2, 3, 4, 5))

    with When(
        "I create covering array",
        description=f"t={strength},k={number_of_parameters},v={value_counts}",
    ):
        covering_array = CoveringArray(parameters=parameters, strength=strength)
        note(str(covering_array))

    with Then("it should cover all t-way combinations"):
        covering_array.check()


@TestFeature
def covering_arrays(self):
    """Covering arrays regression tests."""
    for scenario in loads(current_module(), Scenario):
        scenario()


if main():
    covering_array()
