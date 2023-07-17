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

The `covering(parameters, strength=2)` class allows to calculate a covering array for some `k` parameters having the same or different number of possible values.

The class uses [IPOG], an in-parameter-order, algorithm that as described in [IPOG: A General Strategy for T-Way Software Testing by Yu Lei et al.]

For any non-trivial number of parameters exhaustively testing all possibilities is not possible.
For example, if we have `10` parameters that each has `10` possible values `(k=10, v=10)`, the
number of all possibilities is `10**10 = 10 billion` thus requiring `10 billion` tests for complete coverage.

Given that exhaustive testing might not be practical, a covering array could give us a much smaller
number of tests if we choose to check all possible interactions only between some fixed number
of columns, where an interaction is some specific combination, where order does not matter,
of some `t` number of columns covering all possible values that each selected column could have.

The `covering(parameters, strength=2)`

where,

* `parameters` specifies parameter names as their possible values.
   Specified as a dict[str, list[value]] where key is the parameter name and
   value is a list of possible values for a given parameter.

* `strength` specifies the strength `t` of the covering array that indicates number of columns
   in each combination for which all possible interactions will be checked.
   If `strength` equals number of parameters, then you get the exhaustive case.

For example,

```python
from testflows.combinatorics import covering

parameters = {"a": [0, 1, 2, 3], "b": ["a", "b"], "c": [0, 1, 2], "d": ["d0", "d1"]}

print(covering(parameters, strength=3)
```

give the following output

```bash
CoveringArray({'a': [0, 1, 2, 3], 'b': ['a', 'b'], 'c': [0, 1, 2], 'd': ['d0', 'd1']},3)[
24
a b c d
-------
0 a 0 d0
0 a 1 d1
0 a 2 d0
0 b 0 d1
0 b 1 d0
0 b 2 d1
1 a 0 d1
1 a 1 d0
1 a 2 d1
1 b 0 d0
1 b 1 d1
1 b 2 d0
2 a 0 d0
2 a 1 d1
2 a 2 d0
2 b 0 d1
2 b 1 d0
2 b 2 d1
3 a 0 d0
3 a 1 d1
3 a 2 d0
3 b 0 d1
3 b 1 d0
3 b 2 d1
]
```

### Permutations

### Combinations

#### With Replacement

### Cartesian Product

### Binomial Coefficients

[IPOG]: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=1362e14b8210a766099a9516491693c0c08bc04a
[IPOG: A General Strategy for T-Way Software Testing by Yu Lei et al.]: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=1362e14b8210a766099a9516491693c0c08bc04a
[TestFlows.com Open-Source Software Testing Framework]: https://testflows.com
