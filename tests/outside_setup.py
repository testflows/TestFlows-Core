import functools

from testflows.core import *
from testflows.core.objects import TestBase

@TestScenario
def test(self):
    note("first line in test")

@TestStep(Given)
def presetup(self):
    with Given("I presetup something"):
        pass

    yield

    with By("cleaning up presetup"):
        pass

@TestStep(Given)
@Setup(presetup)
def setup(self):
    with Given("I setup something"):
        pass
    
    yield

    with By("cleaning up something"):
        pass

with Feature("setup parameter"):
    Scenario(test=test, setup=setup)()
