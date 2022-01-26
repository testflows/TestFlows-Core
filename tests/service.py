from testflows.core import *
from testflows.asserts import error, raises

from testflows._core.parallel.service import *


class Test:
    def __init__(self):
        self.x = 2

    def add(self, x, y):
        return x + y


@TestStep(Given)
async def start_service(self, service):
    """Start service.
    """
    async with service as _service:
        yield _service


@TestStep
async def access_attribute(self, o):
    return await o.x


@TestFeature
async def async_service(self):
    """Test async services.
    """
    async with Given("I create local objects"):
        t1 = Test()
        t2 = Test()
    
    async with Scenario("create global process service"):
        service = create_process_service("my service", address=("127.0.0.1", 22222))
    
    async with Scenario("try registering object before starting process service"):
        with raises(ServiceError):
            await service.register(Test())

    async with Given("I create global process service"):
        service = await start_service(service=service)

    async with Scenario("check registering multiple objects"):
        o1 = await service.register(t1)
        o2 = await service.register(t2)
    
    async with Scenario("check trying to register the same object twice"):
        o1_1 = await service.register(t1)
        assert o1.oid == o1_1.oid, error()
        assert o1 == o1_1, error()

    async with Scenario("check using sevice object attribute"):
        r = await o1.x
        assert r == 2, error()

    async with Scenario("check using service object methods"):
        r = await o1.add(2,3)
        assert r == 5, error()
    
    async with Scenario("check using multiple object methods"):
        r = await o1.add(2,3) + await o2.add(3,3)
        assert r == 11, error()

    async with Scenario("check accessing service object attribute from different async loops"):
        r1 = When(test=access_attribute, parallel=True)(o=o1)
        r2 = When(test=access_attribute, parallel=True)(o=o1)

        v1 = (await r1).result.value
        v2 = (await r2).result.value

        assert v1 == '2', error()
        assert v2 == '2', error()


@TestModule
@Name("service")
def feature(self):
    """Check using parallel service.
    """
    Feature(test=async_service)()


if main():
    feature()