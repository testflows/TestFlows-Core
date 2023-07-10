# Copyright 2023 Katteli Inc.
# TestFlows.com Open-Source Software Testing Framework (http://testflows.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import math

from collections import namedtuple
from itertools import product, islice, combinations


class X:
    """Don't care value."""

    pass


def prepare(parameters):
    """Returns parameters set and its map.

    Parameters set is a list[list] where
    first level is indexed keys and second level
    are indexed values for a given parameter.

    Parameters map can be used to convert keys and values
    indexes to actual parameters name and values.

    :param parameters: parameters dictionary dict[str, list[values]])
    """
    keys = list(parameters.keys())

    parameters_set = []
    parameters_map = {}

    for key in keys:
        v = parameters[key]
        v = list(set(v))
        parameters_map[key] = v
        parameters_set.append(list(range(len(v))))

    return parameters_set, parameters_map


def pi_combination_index(t, combination):
    """Return an index for a given combination.
    Combination is represented by a tuple containing
    parameters referenced by their indexes.

    https://stackoverflow.com/questions/37764429/algorithm-for-combination-index-in-array

    f'(5, 3, [2,3,4]) = binom(5-2,3) + binom(5-3,2) + binom(5-4,1) - 1 =
                      = 1 + 1 + 1 - 1 = 2

    :param combination: tuple(parameter index,...)
    """
    N = len(combination)
    index = 0
    for i, k in enumerate(combination):
        index += math.comb(N - k, t - i)
    return index


def combination_values_bitmap_index(combination, values, parameters_set):
    """Return an bit index in the bitmap for a given
    parameter combination and the specific combination of values
    for these parameters.

    Example:
    ```
    >>> for j,i in enumerate(list(itertools.product([0,1,2,3],[0,1,2],[0,1,2]))):
    ...    print(i, 9*i[0] + 3*i[1] + 1*i[2], j)
    [0,1,2,3],[0,1,2],[0,1,2]
    i         j       k
    Jv * Kv = 9
    Kv = 3
    1
    ```

    :param combination: combination of parameters
    :param values: specific combination of values for the parameters
    """
    value_lengths = (len(parameters_set[p]) for p in combination)

    index = 0
    for i, value in enumerate(values):
        index += math.prod(value_lengths[i + 1 :]) * value
    return index


def bitmap_index_combination_values(index, combination, parameters_set):
    """Return values for a given bitmap index and
    combination of parameters.

    Example:
    ```
    (3, 1, 1) 15 15
     5  2  2

    4*i[0] + 2*i[1] + 1*i[2] = 15
    = 15//4 = 3 (15-12) = 3
    = 3//2 = 1 (3 - 2) = 1
    = 1//1 = 1
    = (3,1,1)
    ```

    :param index: bitmap index
    :param combination: combination of parameters
    """
    value_lengths = (len(parameters_set[p]) for p in combination)

    value = [0] * len(combination)

    c = index
    for i in range(len(combination)):
        j = math.prod(value_lengths[i + 1 :])
        value[i] = c // j
        c = c - value[i] * j

    return value


def construct_pi(i, t, parameters_set):
    """Construct a set t-way combinations of values
    involving parameter Pi and t-1 parameters among
    the first i-1 parameters.

    Return pi which is a dictionary of bitmaps where each bit
    represent if parameter value combination is covered (0) or not (1).

    Initially, the bitmap is set to all 1's.
    """
    # create all t-way combinations of Pi with P0 to Pi-1 columns
    t_way_combinations = [c + (i,) for c in combinations(range(i), t - 1)]

    # return pi of bitmaps for each indexed combination of parameters
    # FIXME: value_lengths should be stored
    # FIXME: value coefficients should be stored
    return t_way_combinations, [
        (1 << math.prod([len(parameters_set[p]) for p in combination])) - 1
        for combination in t_way_combinations
    ]

def horizontal_extension():
    """Horizontal extension for parameter Pi."""
    raise NotImplementedError


def vertical_extension():
    """Vertical extension for parameter Pi"""
    raise NotImplementedError


def convert_tests_to_covering_array(tests, parameters_map):
    """Convert tests to covering array.

    Covering array is a list of tests where each test
    is a dictionary of parameter names to values list[dict(name, value)]
    where tests exhaustively cover a chosen level of t-way combinations of
    parameters.
    """
    raise NotImplementedError


def covering_array(parameters, strength=2):
    """Generate covering array of specified `strength`
    for the given `parameters` where parameters
    is a dict[str, list[value]] where key is the parameter name,
    value is a list of values for a given parameter.

    Uses an algorithm described in the following paper

    2007, "IPOG: A General Strategy for T-Way Software Testing" by
    Yu Lei1, Raghu Kacker, D. Richard Kuhn, Vadim Okun, and James Lawrence

    :param parameters: parameters (dict[str, list[values]])
    :param strength: (optional) strength, default: 2
    """
    # t-strength is > 1 and <= number of parameters
    t = max(1, min(strength, len(parameters)))

    # convert parameters dictionary into a parameters set
    # which uses only indexes for parameter names and values
    parameters_set, parameters_map = prepare(parameters)

    print("Parameters map: ", parameters_map)
    print("Parameters set: ", parameters_set)

    # construct first tests using all possible combinations of values
    # for first t-strength parameters
    tests = list(product(*parameters_set[:t]))

    for i in range(t, len(parameters_set)):
        pi_combinations, pi_bitmaps = construct_pi(i=i, t=t, parameters_set=parameters_set)
        print("pi: ", pi_combinations, pi_bitmaps)
    #    #horizontal_extension()
    #    #vertical_extension()

    return tests


if __name__ == "__main__":
    parameters = {"a": [1, 2, 2], "b": ["a", "a", "b", "c", "d"], "c": [10]}
    ca = covering_array(parameters=parameters, strength=2)
    print(ca)
