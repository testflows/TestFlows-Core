from testflows.core import *
from testflows.asserts import error

from steps import *

@TestScenario
def two_number_operation(self, a, op, b, equals):
    """Check operation that takes two numbers"""
    with When(f"I enter number {a}"):
        By(entering_number, args={"num":a})
    with And(f"then press {op}"):
        By(entering_operation, args={"op":op})
    with And(f"then entering {b}"):
        By(entering_number, args={"num":b})
    with And("then press equal"):
        By(entering_equal)
    expected = equals
    with Then(f"the result should be {equals}"):
        By(checking_result, args={"expected":equals})

@TestScenario
@Examples(
    "a op b equals", [
        (2, '+', 2, 4),
        (0, '+', 0, 0),
        (-1, '-', 0, -1),
        (1234234, '+', 0, 1234234),
        (1234567890, '*', 0, 0),
        (4, '/', 2, 2)
    ]
)
def two_number_operations(self):
    for example in self.examples:
        name = '{a}{op}{b}={equals}'.format(**example._asdict())
        run(test=two_number_operation, name=name, args=example._asdict())

@TestFeature
def calculator(self):
    """Calculator.
    """
    run(test=two_number_operations)

map = maps(calculator, ins=[entering_number, entering_operation, entering_equal], outs=[checking_result])

if main():
    run(test=calculator, map=map)
