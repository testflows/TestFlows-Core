import random

from testflows.core import *
from testflows.asserts import error
from testflows.connect import Shell

from requirements import *


@TestScenario
@Requirements(RQ_SRS001_CU_LS_Default_Directory("1.0"))
def list_current_working_directory(self):
    """Check that `ls` utility when run without
    any arguments lists the contents of the
    current working directory.
    """
    shell = self.context.shell

    with When("I execute `ls` command without arguments"):
        r = shell("ls")

    with Then("exitcode should be 0"):
        assert r.exitcode == 0, error()

    with And("it should list the contents of the current working directory"):
        assert "regression.py" in r.output, error()

    metric("metric", random.random(), "ms")


@TestModule
@Name("ls")
@Requirements(RQ_SRS001_CU_LS("1.0"))
def regression(self):
    """The `ls` utility regression module."""
    with Shell() as shell:
        self.context.shell = shell

        Scenario(run=list_current_working_directory)


if main():
    regression()
