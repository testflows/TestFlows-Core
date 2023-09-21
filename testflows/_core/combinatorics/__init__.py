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
import itertools

from .covering_array import CoveringArray, CoveringArrayError

product = itertools.product
permutations = itertools.permutations
binomial = math.comb


def combinations(iterable, r, with_replacement=False):
    """Return successive r-length combinations of elements in the iterable.

    By default, returns combinations without replacement
    unless `with_replacement` is set to `True`.

    For example,

    without replacement

    ```
    combinations(range(4), 3) --> (0,1,2), (0,1,3), (0,2,3), (1,2,3)
    ```

    with replacement

    ```
    combinations(range(4), 3, with_replacement=True) -->
    [(0, 0, 0), (0, 0, 1), (0, 0, 2), (0, 0, 3), (0, 1, 1), (0, 1, 2),
     (0, 1, 3), (0, 2, 2), (0, 2, 3), (0, 3, 3), (1, 1, 1), (1, 1, 2),
     (1, 1, 3), (1, 2, 2), (1, 2, 3), (1, 3, 3), (2, 2, 2), (2, 2, 3),
     (2, 3, 3), (3, 3, 3)]
    ```

    :param iterable: iterable
    :param r: r-length
    :param with_replacement: with replacement, default: `False`
    """
    if with_replacement:
        return itertools.combinations_with_replacement(iterable, r)
    return itertools.combinations(iterable, r)
