from testflows.core import *


@TestModule
@Name("xout flags")
def regression(self):
    with Scenario("XOK when OK", flags=XOK):
        pass

    with Scenario("XFAIL when Fail", flags=XFAIL):
        fail("boo")

    with Scenario("XERROR when Error", flags=XERROR):
        err("boo")

    with Scenario("XNULL when Null", flags=XNULL):
        null("boo")


if main():
    regression()
