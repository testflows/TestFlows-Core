from testflows.core import *


@TestModule
@Name("eresult flags")
def regression(self):
    with Scenario("EFAIL when Fail", flags=EFAIL):
        fail("boo")

    with Scenario("EOK when OK", flags=EOK):
        ok("boo")

    with Scenario("EERROR when Error", flags=EERROR):
        err("boo")

    with Scenario("ESKIP when Skip", flags=ESKIP):
        skip("boo")

    with Scenario("EFAIL when not Fail", flags=EFAIL | XFAIL):
        ok("boo")

    with Scenario("EOK when not OK", flags=EOK | XFAIL):
        fail("boo")

    with Scenario("EERROR when not Error", flags=EERROR | XFAIL):
        ok("boo")

    with Scenario("ESKIP when not Skip", flags=ESKIP | XFAIL):
        ok("boo")


if main():
    regression()
