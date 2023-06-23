#!/usr/bin/env python3
import time
import asyncio

from testflows.core import *
from testflows.asserts import error


@TestStep
async def async_step(self, delay=0):
    debug(self.name)
    await asyncio.sleep(delay)
    debug(f"{self.name} -- done")
    return "done"


@TestScenario
def non_async_test(self, delay=0):
    debug(self.name)
    time.sleep(delay)
    return "done"


@TestScenario
def non_async_test_with_async_test_function(self, delay=0):
    async_pool = AsyncPool()
    current().executor = async_pool

    debug(self.name)
    Test(test=async_test, parallel=True, executor=async_pool, name="test1")(delay=1)
    Test(test=async_test, parallel=True, executor=async_pool, name="test2")(delay=1)
    Test(test=async_test, parallel=True, name="test3")(delay=1)

    async_test(delay=1)
    async_test(delay=1)
    async_test(delay=1)

    assert len(join()) == 3, error()
    return "done"


@TestScenario
def non_async_test_with_parallel_non_async_test(self, delay=0):
    debug(self.name)
    Test(run=non_async_test, parallel=True)
    join()


@TestScenario
async def async_test(self, delay=0):
    debug(self.name)
    await asyncio.sleep(delay)
    return "done"


@TestFeature
async def async_test_in_async_test(self):
    """Check running async tests inside
    an async test.
    """
    async with Scenario("run async test as function"):
        assert await async_test() == "done"

    async with Scenario("run async test as Test(run=...)"):
        assert (await Test(run=async_test)).value == "done"

    async with Scenario("run async test as Test(test=...)"):
        assert (await Test(test=async_test)()).value == "done"

    return "done"


@TestFeature
async def in_async(self):
    async with Scenario("run non async test as function not awaited"):
        non_async_test()
        assert await current().futures[0] == "done"

    async with Scenario("run non async test as function awaited"):
        assert (await non_async_test()) == "done"

    async with Scenario("run non async test as function joined"):
        non_async_test()
        assert (await join())[0] == "done"

    async with Scenario("run parallel non async test without specified executor"):
        assert (await Test(run=non_async_test, parallel=True)).value == "done"

    async with Scenario("run parallel non async test with specified executor"):
        with Pool() as executor:
            assert (
                await Test(run=non_async_test, parallel=True, executor=executor)
            ).value == "done"

    async with Scenario("run parallel non async test with specified async executor"):
        with AsyncPool() as executor:
            assert (
                await Test(run=non_async_test, parallel=True, executor=executor)
            ).value == "done"

    async with Scenario(
        "run parallel non async test when test has default executor set to async"
    ):
        with AsyncPool() as executor:
            current().executor = executor
            assert (await Test(run=non_async_test, parallel=True)).value == "done"

    async with Scenario("run non parallel async test"):
        assert (await async_test()) == "done"

    async with Scenario("run non parallel inline test with steps"):
        async with Step("simple step"):
            pass

        async with Step("run step as function"):
            assert (await async_step(delay=0.1)) == "done"

        for i in range(10):
            assert (await Step(run=async_step, name=f"step {i}")).value == "done"

    async with Scenario("run non parallel inline test with parallel async steps"):
        for i in range(10):
            Step(run=async_step, name=f"step {i}", parallel=True, args={"delay": 1})
        await join()

    async with Scenario("run parallel async test without specified executor"):
        Scenario(test=async_test, parallel=True)()
        assert (await join())[0].value == "done"

    async with Scenario("run parallel async test with specified executor"):
        with AsyncPool() as async_pool:
            Scenario(test=async_test, parallel=True, executor=async_pool)()
            assert (await join())[0].value == "done"
        joined = await join()
        assert joined == [], error()

    async with Scenario("run parallel async test with specified thread executor"):
        with Pool() as pool:
            f = Scenario(test=async_test, parallel=True, executor=pool)()
            await join()
        assert (await f).value == "done"


@TestFeature
def in_thread(self):
    with Scenario("run async test as function"):
        assert async_test() == "done"

    with Scenario("run async test as Test(run=...)"):
        assert Test(run=async_test).value == "done"

    with Scenario("run async test as Test(test=...)()"):
        assert Test(test=async_test)().value == "done"

    with Scenario("run async test using with"):
        try:
            with async_test:
                pass
        except AttributeError as e:
            assert str(e) == "__enter__"
        try:
            with async_test():
                pass
        except AttributeError as e:
            assert str(e) == "__enter__"

    with Feature("run async test that executes another async test as function"):
        assert async_test_in_async_test() == "done"

    with Scenario("run parallel async test without specified executor"):
        assert Test(run=async_test, parallel=True).result().value == "done"

    with Scenario("run parallel async test with specified executor"):
        with AsyncPool() as async_pool:
            assert (
                Test(run=async_test, parallel=True, executor=async_pool).result().value
                == "done"
            )

    with Scenario("run parallel async test with specified executor of wrong type"):
        with Pool() as pool:
            assert (
                Test(run=async_test, parallel=True, executor=pool).result().value
                == "done"
            )

    with Scenario("run multiple parallel async test with specified executor"):
        with AsyncPool() as async_pool:
            t0 = Test(
                test=async_test, parallel=True, executor=async_pool, name="test0"
            )(delay=1)
            t1 = Test(
                test=async_test, parallel=True, executor=async_pool, name="test1"
            )(delay=1)
            t2 = Test(
                test=async_test, parallel=True, executor=async_pool, name="test2"
            )(delay=1)
            assert t0.result().value == "done"
            assert t1.result().value == "done"
            assert t2.result().value == "done"

    with Scenario(
        "run multiple parallel async test with specified executor with joins"
    ):
        with AsyncPool() as async_pool:
            t0 = Test(
                test=async_test, parallel=True, executor=async_pool, name="test0"
            )(delay=1)
            assert join(t0)[0].value == "done"
            t1 = Test(
                test=async_test, parallel=True, executor=async_pool, name="test1"
            )(delay=1)
            t2 = Test(
                test=async_test, parallel=True, executor=async_pool, name="test2"
            )(delay=1)
            for r in join():
                assert r.value == "done"


with Module("regression"):
    Feature(run=in_thread, parallel=True)
    Feature(run=in_async, parallel=True)

    with Feature("global parallel pool"):
        with Scenario("parallel thread pool check deadlock"):
            Test(run=non_async_test_with_parallel_non_async_test, parallel=True)
            join()

        with Scenario("parallel async pool"):
            non_async_test_with_async_test_function()
