from testflows.core import *
from testflows.combinatorics import CoveringArray, product
from testflows.asserts import snapshot, error
from testflows.asserts import values as assert_values


@TestSketch(Scenario)
def homogeneous(self):
    """Check generating covering arrays for different strength and
    different number of parameters with different number of homogeneous values
    where homogeneous values means that each parameter has the same number of values.

    Where,

    *  number of values for each parameter is either 1,2,3
    *  number of parameters is either 1,2,3,4,5,6
    *  strength is either 1,2,3,4,5
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

    with And("it should match the snapshot"):
        with assert_values() as that:
            assert that(
                snapshot(
                    covering_array,
                    name=f"t={strength},k={number_of_parameters},v={len(values)}",
                    encoder=str,
                )
            ), error()


@TestSketch(Scenario)
def heterogeneous(self):
    """Check generating covering arrays for different strength and
    different number of parameters with different number of heterogeneous values
    where heterogeneous values means that different parameters have different number of values.

    Where,

    *  number of parameters is either 2,3,4
    *  number of values for each parameter is either 1,2,3
    *  strength is either 1,2,3,4,5
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

    with And("it should match the snapshot"):
        with assert_values() as that:
            assert that(
                snapshot(
                    covering_array,
                    name=f"t={strength},k={number_of_parameters},v={value_counts}",
                    encoder=str,
                )
            ), error()


@TestFeature
def covering_arrays(self):
    """Regression tests for covering arrays."""
    for scenario in loads(current_module(), Scenario):
        scenario()


if main():
    covering_arrays()
