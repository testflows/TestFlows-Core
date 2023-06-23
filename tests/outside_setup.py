import functools

from testflows.core import *
from testflows.asserts import error


@TestScenario
def test(self):
    note("first line in test")

    assert self.parent.name == "/setup parameter", error()


@TestStep(Given)
def presetup(self):
    with Given("I presetup something"):
        pass

    yield

    with By("cleaning up presetup"):
        pass


@TestStep(Given)
@Setup(presetup)
def setup(self, arg):
    with Given("I setup something"):
        pass

    assert self.parent.name == "/setup parameter/test", error()

    yield

    with By("cleaning up something"):
        pass


with Feature("setup parameter"):
    Scenario(test=test, setup=Given(test=setup, args={"arg": "foo"}))()
