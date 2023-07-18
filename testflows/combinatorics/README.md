## [TestFlows.com Open-Source Software Testing Framework] Combinatorics


The `testflows.combinatorics` module provides a convenient collection of tools
used for combinatorial testing to check different combinations of the input parameters.

## Why

Provides support for calculating the following:

* covering arrays based on the [IPOG] algorithm.
  Covering arrays are a generalization of pairwise testing also known as all-pairs testing.
  Also known as n-wise testing.
* permutations of input parameters
* combinations with and without replacement
* cartesian product of input iterables
* binomial coefficients

## Installation

When used with [TestFlows.com Open-Source Software Testing Framework] the `testflows.combinatorics` module
comes by default as a part of the `testflows.core` module. However, if you would like to use
it with other test frameworks, it can be installed separately as follows:

```bash
pip3 install --update testflows.combinatorics
```

## Usage

### Covering Arrays

The `covering(parameters, strength=2)` class allows to calculate a covering array
for some `k` parameters having the same or different number of possible values.

The class uses [IPOG], an in-parameter-order, algorithm as described in [IPOG: A General Strategy for T-Way Software Testing by Yu Lei et al.]

For any non-trivial number of parameters exhaustively testing all possibilities is not feasible.
For example, if we have `10` parameters that each has `10` possible values `(k=10, v=10)`, the
number of all possibilities is `10**10 = 10 billion` thus requiring `10 billion` tests for complete coverage.

Given that exhaustive testing might not be practical, a covering array could give us a much smaller
number of tests if we choose to check all possible interactions only between some fixed number
of columns at least once, where an interaction is some specific combination, where order does not matter,
of some `t` number of columns covering all possible values that each selected column could have.

> You can find out more about covering array by visiting US National Institute of Standards and Technology's (NIST)
> [Introduction to Covering Arrays](https://math.nist.gov/coveringarrays/coveringarray.html) page.

The `covering(parameters, strength=2)` takes the following arguments

where,

* `parameters` specifies parameter names and their possible values and
   is specified as a `dict[str, list[value]]`, where key is the parameter name and
   value is a list of possible values for a given parameter.
* `strength` specifies the strength `t` of the covering array that indicates the number of columns
   in each combination for which all possible interactions will be checked.
   If `strength` equals the number of parameters, then you get the exhaustive case.

The return value of the `covering(parameters, strength=2)` is a `CoveringArray` object that is an iterable
of tests, where each test is a dictionary with each key being the parameter name and its value
being the parameter value.

For example,

```python
from testflows.combinatorics import covering

parameters = {"a": [0, 1], "b": ["a", "b"], "c": [0, 1, 2], "d": ["d0", "d1"]}

print(covering(parameters, strength=2)
```

gives the following output

```bash
CoveringArray({'a': [0, 1], 'b': ['a', 'b'], 'c': [0, 1, 2], 'd': ['d0', 'd1']},2)[
6
a b c d
-------
0 b 2 d1
0 a 1 d0
1 b 1 d1
1 a 2 d0
0 b 0 d0
1 a 0 d1
]
```

Given that in the example above the `strength=2`, all possible 2-way (pairwise)
combinations of parameters `a`, `b`, `c`, and `d` are the following:

```python
[('a', 'b'), ('a', 'c'), ('a', 'd'), ('b', 'c'), ('b', 'd'), ('c', 'd')]
```

The six tests that make up the covering array cover all the possible interactions
between values of each of these parameter combinations. For example, the `('a', 'b')`
parameter combination covers all possible combinations of the values that
parameter `a` and `b` can take.

Given that parameter `a` can have values `[0, 1]`, and parameter `b` can have values `['a', 'b']`
all possible interactions are the following:

```python
[(0, 'a'), (0, 'b'), (1, 'a'), (1, 'b')]
```

where the first element of each tuple corresponds to the value of the parameter `a`, and the second
element corresponds to the value of the parameter `b`.

Examining the covering array above we can see that all possible interactions of parameters
`a` and `b` are indeed covered at least once. The same check can be done for other parameter combination.

#### Checking Covering Array

The `check()` method of the `CoveringArray` can be used to verify that the tests
inside the covering array do verify all possible t-way interactions at least once and thus
meet the definition of a covering array.

For example,

```python
from testflows.combinatorics import covering

parameters = {"a": [0, 1], "b": ["a", "b"], "c": [0, 1, 2], "d": ["d0", "d1"]}
tests = covering(parameters, strength=2)

print(tests.check())
```

#### Dumping Covering Array

The `CoveringArray` object implements custom `__str__` method and therefore it can be easily converted into
a string representation similar to the [NIST covering array tables](https://math.nist.gov/coveringarrays/ipof/ipof-results.html).

For example,

```python
print(covering(parameters, strength=2)
```

### Combinations

The `combinations(iterable, r, with_replacement=False)` function can be used to calculate
all r-length combinations of elements in a specified iterable.

For example,

```python3
from testflows.combinatorics import combinations

parameters = {"a": [0, 1], "b": ["a", "b"], "c": [0, 1, 2], "d": ["d0", "d1"]}

print(list(combinations(parameters.keys(), 2)))
```

```python3
[('a', 'b'), ('a', 'c'), ('a', 'd'), ('b', 'c'), ('b', 'd'), ('c', 'd')]
```

> This function is equivalent to the [itertools.combinations](https://docs.python.org/3/library/itertools.html#itertools.combinations).

#### With Replacement

You can calculate all combinations with replacement by setting the `with_replacement` argument to `True`.

For example,

```python3
from testflows.combinatorics import combinations

parameters = {"a": [0, 1], "b": ["a", "b"], "c": [0, 1, 2], "d": ["d0", "d1"]}

print(list(combinations(parameters.keys(), 2, with_replacement=True)))
```

```python3
[('a', 'a'), ('a', 'b'), ('a', 'c'), ('a', 'd'), ('b', 'b'), ('b', 'c'), ('b', 'd'), ('c', 'c'), ('c', 'd'), ('d', 'd')]
```

> The `with_replacement=True` option is equivalent to [itertools.combinations_with_replacement](https://docs.python.org/3/library/itertools.html#itertools.combinations_with_replacement).

### Cartesian Product

You can calculate all possible combinations of elements from different iterables using
the cartesian `product(*iterables, repeat=1)` function.

For example,

```python3
from testflows.combinatorics import *

parameters = {"a": [0, 1], "b": ["a", "b"], "c": [0, 1, 2], "d": ["d0", "d1"]}

print(list(product(parameters["a"], parameters["b"])))
```

```python3
[(0, 'a'), (0, 'b'), (1, 'a'), (1, 'b')]
```

> This function is equivalent to the [itertools.product](https://docs.python.org/3/library/itertools.html#itertools.product).


### Permutations

The `permutations(iterable, r=None)` function can be used to calculate
the r-length permutations of elements for a given iterable.

> Permutations are different from `combinations`. In a combination the elements
> don't have any order but in a permutation elements order is important.

For example,

```python3
from testflows.combinatorics import *

parameters = {"a": [0, 1], "b": ["a", "b"], "c": [0, 1, 2], "d": ["d0", "d1"]}

print(list(permutations(parameters.keys(), 2)))
```

```python3
('a', 'b'), ('a', 'c'), ('a', 'd'), ('b', 'a'), ('b', 'c'), ('b', 'd'), ('c', 'a'), ('c', 'b'), ('c', 'd'), ('d', 'a'), ('d', 'b'), ('d', 'c')]
```

and as we can see both `('a', 'b')` and `('b', 'a')` elements are present.


### Binomial Coefficients

You can calculate binomial coefficient which is the same as
the number of ways to choose `k` items from `n` items without repetition and without order.

> n! / (k! * (n - k)!) when k <= n and is zero when k > n

For example,

```python3
from testflows.combinatorics import *

print(binomial(4,2))
```

```python3
6
```

which means that there are 6 ways to choose 2 elements out of 4.

> This function is equivalent to the [math.comb](https://docs.python.org/3/library/math.html#math.comb).

[IPOG]: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=1362e14b8210a766099a9516491693c0c08bc04a
[IPOG: A General Strategy for T-Way Software Testing by Yu Lei et al.]: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=1362e14b8210a766099a9516491693c0c08bc04a
[TestFlows.com Open-Source Software Testing Framework]: https://testflows.com
