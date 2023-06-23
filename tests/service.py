from testflows.core import *
from testflows.asserts import error, raises

from testflows._core.parallel.service import *


class Test:
    def __init__(self):
        self.x = 2

    def add(self, x, y):
        return x + y


@TestStep
async def access_attribute(self, o):
    return await o.x


@TestStep
def sync_access_attribute(self, o):
    return o.x


@TestFeature
async def async_service(self):
    """Test service in async code."""
    async with Given("I create local objects"):
        t1 = Test()
        t2 = Test()

    async with Scenario("create global process service"):
        service = process_service()

    async with Scenario("check registering multiple objects"):
        o1 = await service.register(t1)
        o2 = await service.register(t2)

    async with Scenario("check trying to register the same object twice"):
        o1_1 = await service.register(t1)
        assert o1.oid == o1_1.oid, error()
        assert o1 == o1_1, error()

    async with Scenario("check using sevice object attribute"):
        r = o1.x
        r = await r
        assert r == 2, error()

    async with Scenario("check using service object methods"):
        r = await o1.add(2, 3)
        assert r == 5, error()

    async with Scenario("check using multiple object methods"):
        r = await o1.add(2, 3) + await o2.add(3, 3)
        assert r == 11, error()

    async with Scenario(
        "check accessing service object attribute from different async loops"
    ):
        r1 = When(test=access_attribute, parallel=True)(o=o1)
        r2 = When(test=access_attribute, parallel=True)(o=o1)

        v1 = (await r1).value
        v2 = (await r2).value

        assert v1 == "2", error()
        assert v2 == "2", error()

    async with Scenario("check basic registered object garbage collection"):
        o1 = await service.register(Test())
        oid = o1.oid
        assert oid in service.objects, error()
        del o1
        await asyncio.sleep(0.1)
        assert oid not in service.objects, error()


@TestFeature
def sync_service(self):
    """Test service in sync code."""
    with Given("I create local objects"):
        t1 = Test()
        t2 = Test()

    with Scenario("create global process service"):
        service = process_service()

    with Scenario("check registering multiple objects"):
        o1 = service.register(t1)
        o2 = service.register(t2)

    with Scenario("check trying to register the same object twice"):
        o1_1 = service.register(t1)
        assert o1.oid == o1_1.oid, error()
        assert o1 == o1_1, error()

    with Scenario("check using sevice object attribute"):
        r = o1.x
        assert r == 2, error()

    with Scenario("check using service object methods"):
        r = o1.add(2, 3)
        assert r == 5, error()

    with Scenario("check using multiple object methods"):
        r = o1.add(2, 3) + o2.add(3, 3)
        assert r == 11, error()

    with Scenario(
        "check accessing service object attribute from different async loops"
    ):
        r1 = When(test=sync_access_attribute, parallel=True)(o=o1)
        r2 = When(test=sync_access_attribute, parallel=True)(o=o1)

        v1 = r1.result().value
        v2 = r2.result().value

        assert v1 == "2", error()
        assert v2 == "2", error()

    with Scenario("create service object that exposes magic methods"):
        l1 = service.register(
            list(),
            expose=ExposedMethodsAndProperties(
                methods=(
                    "__add__",
                    "__contains__",
                    "__delitem__",
                    "__getitem__",
                    "__len__",
                    "__mul__",
                    "__reversed__",
                    "__rmul__",
                    "__setitem__",
                    "append",
                    "count",
                    "extend",
                    "index",
                    "insert",
                    "pop",
                    "remove",
                    "reverse",
                    "sort",
                    "__imul__",
                ),
                properties=tuple(),
            ),
        )
        l1.append("a")
        assert l1[0] == "a", error()

    with Scenario("check basic registered object garbage collection"):
        o1 = service.register(Test())
        oid = o1.oid
        assert oid in service.objects, error()
        del o1
        assert oid not in service.objects, error()


@TestModule
@Name("service")
def feature(self):
    """Check using parallel service."""
    Feature(test=async_service)()
    Feature(test=sync_service)()


if main():
    feature()
