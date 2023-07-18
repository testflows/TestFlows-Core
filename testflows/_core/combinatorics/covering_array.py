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
import sys
import math

from collections import namedtuple
from itertools import product, islice, combinations


class CoveringArrayError(Exception):
    """Covering array error."""

    def __init__(self, combination, values):
        self.combination = combination
        self.values = values

    def __str__(self):
        return f"missing combination={self.combination},values={self.values}"


class X:
    """Don't care value."""

    pass


BestTest = namedtuple("BestTest", "test coverage bitmap")
Π = namedtuple("Π", "combinations bitmap")


class CoveringArray:
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

    def __init__(self, parameters, strength=2):
        self.parameters = parameters
        self.strength = strength
        self.array = self.generate()

    def __iter__(self):
        return iter(self.array)

    def prepare(self):
        """Returns parameters set and its map.

        Parameters set is a list[list] where
        first level is indexed keys and second level
        are indexed values for a given parameter.

        Parameters map can be used to convert keys and values
        indexes to actual parameters name and values.

        :param parameters: parameters dictionary dict[str, list[values]])
        """
        keys = list(self.parameters.keys())

        parameters_set = []
        parameters_map = {}

        for key in keys:
            v = self.parameters[key]
            v = list(set(v))
            parameters_map[key] = v
            parameters_set.append(list(range(len(v))))

        return parameters_set, parameters_map

    def combination_index(self, t, N, combination):
        """Return an index for a given combination in π.
        Combination is represented by a tuple containing
        parameters referenced by their indexes.

        https://stackoverflow.com/questions/37764429/algorithm-for-combination-index-in-array

        f(5, 3, [2,3,4]) = binom(5,3) - binom(5-2,3) - binom(5-3,2) - binom(5-4,1) =
                         = 10 - 1 - 1 - 1 = 6

        :param combination: tuple(parameter index,...)
        """

        t -= 1
        index = math.comb(N, t) - 1
        for i, p in enumerate(combination[:-1]):
            p += 1
            index -= math.comb(N - p, t - i)

        return index

    def combination_values_bitmap_index(self, combination, values):
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
        value_lengths = [len(self.parameters_set[p]) for p in combination]

        index = 0
        for i, value in enumerate(values):
            index += math.prod(value_lengths[i + 1 :]) * value
        return index

    def bitmap_index_combination_values(self, index, combination):
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
        value_lengths = [len(self.parameters_set[p]) for p in combination]

        value = [0] * len(combination)

        c = index
        for i in range(len(combination)):
            j = math.prod(value_lengths[i + 1 :])
            value[i] = c // j
            c = c - value[i] * j

        return value

    def construct_π(self, i, t):
        """Construct a set t-way combinations of values
        involving parameter Pi and t-1 parameters among
        the first i-1 parameters.

        Return pi which is a dictionary of bitmaps where each bit
        represent if parameter value combination is covered (0) or not (1).

        Initially, the bitmap is set to all 1's.
        """
        # create all t-way combinations of Pi with P0 to Pi-1 columns
        t_way_combinations = [c + (i,) for c in combinations(range(i), t - 1)]

        # FIXME: value_lengths should be stored
        # FIXME: value coefficients should be stored
        π = Π(
            t_way_combinations,
            [
                (1 << math.prod([len(self.parameters_set[p]) for p in combination])) - 1
                for combination in t_way_combinations
            ],
        )
        return π

    def horizontal_extension(self, t, i, π):
        """Horizontal extension for parameter Pi."""

        # for each test τ = (v1, v2, …, vi-1) in tests
        for τ in range(len(self.tests)):
            test = self.tests[τ]
            # choose a value vi of Pi and replace τ with τ’ = (v1, v2, …, vi-1, vi) so that τ’ covers the
            # most number of combinations of values in π
            best = None
            # FIXME: if bitmap is all empty set value to don't care and don't try to pick any value

            for value in self.parameters_set[i]:
                new_test = test + [value]
                coverage, bitmap = self.calculate_coverage(t, i, new_test, π)
                if best is None or coverage >= best.coverage:
                    best = BestTest(new_test, coverage, bitmap)
            self.tests[τ] = best.test
            π = Π(π.combinations, best.bitmap)

        return π

    def vertical_extension(self, t, i, π):
        """Vertical extension for parameter Pi"""

        # for each combination of σ in π
        for combination in π.combinations:
            index = self.combination_index(t, i, combination)

            bitmap = π.bitmap[index]
            bitmap_index = -1

            if bitmap == 0:
                continue

            while bitmap:
                bitmap_index += 1
                if not bitmap & 1:
                    bitmap >>= 1
                    continue
                bitmap >>= 1

                values = self.bitmap_index_combination_values(bitmap_index, combination)

                covered = False

                for test in self.tests:
                    test_values = self.combination_values(test, combination)
                    if values == test_values:
                        # already covered
                        covered = True
                        break

                    # not covered, so either change an existing test, if possible
                    change_existing = True
                    for value, test_value in zip(values, test_values):
                        if value == test_value:
                            continue
                        elif test_value is X:
                            continue
                        else:
                            change_existing = False

                    if change_existing:
                        self.set_combination_values(test, values, combination)
                        covered = True
                        break

                if covered:
                    # move to the next combination of values
                    continue

                # or otherwise add a new test to cover σ and remove it from π
                new_test = [X] * len(self.parameters_set[: i + 1])
                self.set_combination_values(new_test, values, combination)
                self.tests.append(new_test)

        # replace all X with the first value for a given parameter
        for test in self.tests:
            for i, p in enumerate(test):
                if p is not X:
                    continue
                test[i] = self.parameters_set[i][0]

    def convert_tests_to_covering_array(self):
        """Convert tests to covering array.

        Covering array is a list of tests where each test
        is a dictionary of parameter names to values list[dict(name, value)]
        where tests exhaustively cover a chosen level of t-way combinations of
        parameters.

        Example:
        Parameters map:  {'a': [1, 2], 'b': ['b', 'd', 'c', 'a'], 'c': [10]}

        """
        ca = []
        parameter_names = list(self.parameters_map.keys())

        for test in self.tests:
            ca_test = {}
            for i, p in enumerate(test):
                parameter_name = parameter_names[i]
                ca_test[parameter_name] = self.parameters_map[parameter_name][p]
            ca.append(ca_test)

        return ca

    def combination_values(self, test, combination):
        """Return values of the combination covered by a given test."""
        values = [0] * len(combination)

        for i, parameter in enumerate(combination):
            values[i] = test[parameter]

        return values

    def set_combination_values(self, test, values, combination):
        """Set test values for a given combination."""
        for i, parameter in enumerate(combination):
            test[parameter] = values[i]

    def calculate_coverage(self, t, i, test, π):
        """Calculate coverage of the test for a given π combinations."""
        coverage = 0

        new_bitmap = list(π.bitmap)

        for combination in π.combinations:
            index = self.combination_index(t, i, combination)
            bitmap = π.bitmap[index]

            current_coverage = (bitmap).bit_count()

            values = self.combination_values(test, combination)

            bitmap_index = self.combination_values_bitmap_index(combination, values)

            bitmap = bitmap & ~(1 << bitmap_index)
            new_coverage = (bitmap).bit_count()
            coverage += current_coverage - new_coverage

            new_bitmap[index] = bitmap

        return coverage - current_coverage, new_bitmap

    def generate(self):
        """Generate covering array."""
        # t-strength is > 1 and <= number of parameters
        t = max(1, min(self.strength, len(self.parameters)))

        # convert parameters dictionary into a parameters set
        # which uses only indexes for parameter names and values
        self.parameters_set, self.parameters_map = self.prepare()

        # construct first tests using all possible combinations of values
        # for the first t-strength parameters
        self.tests = list(product(*self.parameters_set[:t]))

        for i in range(len(self.tests)):
            self.tests[i] = list(self.tests[i])

        for i in range(t, len(self.parameters_set)):
            π = self.construct_π(i=i, t=t)
            π = self.horizontal_extension(t, i, π)
            self.vertical_extension(t, i, π)

        return self.convert_tests_to_covering_array()

    def check(self):
        """Returns True if covering array covers all t-strength
        combination of the parameters or raises an error."""
        t = self.strength

        if not self.array:
            raise ValueError("covering array is empty")

        parameter_names = list(self.parameters.keys())

        for combination in combinations(parameter_names, self.strength):
            for values in product(
                *[self.parameters[parameter] for parameter in combination]
            ):
                covered = True
                for test in self.array:
                    covered = True
                    for i, parameter in enumerate(combination):
                        if test[parameter] != values[i]:
                            covered = False
                            break
                    if covered:
                        break
                if not covered:
                    raise CoveringArrayError(combination, values)

        return True

    def __str__(self):
        """Dump covering array representation to string."""
        lines = [f"CoveringArray({self.parameters},{self.strength})["]
        lines.append(f"{len(self.array)}")
        header = " ".join(str(v) for v in self.array[0].keys())

        lines.append(header)
        lines.append("-" * len(header))

        for test in self.array:
            lines.append(" ".join(str(v) for v in test.values()))
        lines.append("]")

        return "\n".join(lines)
