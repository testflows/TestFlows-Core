from testflows.core import *


@TestOutline
def outline(self, fails=False):
    note("my outline")
    if fails:
        fail("failed")


@TestScenario
def xflags_when_parameter(self):
    Check(
        name="should be skipped",
        run=outline,
        xflags={"": (SKIP, None, lambda test: True)},
    )
    Check(name="should run", run=outline, xflags={"": (SKIP, None, lambda test: False)})
    Check(
        name="should be skipped without when condition",
        run=outline,
        xflags={"": (SKIP, None)},
    )


@TestScenario
def xfails_when_parameter(self):
    Check(
        name="should be crossed out",
        test=outline,
        xfails={"": [(Fail, "reason", lambda test: True)]},
    )(fails=True)
    Check(
        name="should not be crossed out",
        test=outline,
        xfails={"": [(Fail, "reason", lambda test: False)]},
    )(fails=True)


@TestFeature
def feature(self):
    for scenario in loads(current_module(), Scenario):
        scenario()


if main():
    feature()
