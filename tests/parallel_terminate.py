import time
import random
import asyncio

from testflows.core import *


@TestStep(Given)
def setup(self, result_type=OK):
    """Setup step."""
    try:
        yield
    finally:
        with By("cleaning up setup"):
            result(type=result_type)


@TestStep(Given)
async def async_setup(self, result_type=OK):
    """Setup step."""
    try:
        yield
    finally:
        async with By("cleaning up setup"):
            result(type=result_type)


@TestScenario
def scenario(self, sleep=None, result_type=OK):
    with Given("I perform setup"):
        setup(result_type=result_type)

    with When("I perform action"):
        i = 0
        while sleep > 0:
            with By(f"sleeping #{i}"):
                time.sleep(0.1)
            i += 1
            sleep -= 0.1

    with Then("I set the result"):
        result(type=result_type)


@TestScenario
async def async_scenario(self, sleep=None, result_type=OK):
    async with Given("I perform setup"):
        await async_setup(result_type=result_type)

    async with When("I perform action"):
        i = 0
        while sleep > 0:
            async with By(f"sleeping #{i}"):
                await asyncio.sleep(0.1)
            i += 1
            sleep -= 0.1

    async with Then("I set the result"):
        result(type=result_type)


@TestSuite
def suite(self, executor, with_join=False):
    with executor(5) as pool:
        for i in range(1):
            Scenario(
                test=scenario, name=f"{i} scenario - pass", parallel=True, executor=pool
            )(sleep=1, result_type=OK)
            Scenario(
                test=scenario,
                name=f"{i} scenario - fail",
                parallel=True,
                executor=pool,
                flags=TE,
            )(sleep=1, result_type=Fail)
            Scenario(
                test=scenario,
                name=f"{i} scenario - pass 2",
                parallel=True,
                executor=pool,
            )(sleep=1, result_type=OK)
            Scenario(
                test=scenario,
                name=f"{i} scenario - pass 3",
                parallel=True,
                executor=pool,
            )(sleep=1, result_type=OK)
            Scenario(
                test=scenario,
                name=f"{i} scenario - pass 4",
                parallel=True,
                executor=pool,
            )(sleep=1, result_type=OK)
        if with_join:
            join()


@TestSuite
async def async_suite(self, executor, with_join=False):
    with executor(5) as pool:
        Scenario(
            test=async_scenario, name=f"scenario - pass", parallel=True, executor=pool
        )(sleep=1, result_type=OK)
        Scenario(
            test=async_scenario, name=f"scenario - fail", parallel=True, executor=pool
        )(sleep=1, result_type=Fail)
        Scenario(
            test=async_scenario, name=f"scenario - pass 2", parallel=True, executor=pool
        )(sleep=1, result_type=OK)
        Scenario(
            test=async_scenario, name=f"scenario - pass 3", parallel=True, executor=pool
        )(sleep=1, result_type=OK)
        Scenario(
            test=async_scenario, name=f"scenario - pass 4", parallel=True, executor=pool
        )(sleep=1, result_type=OK)

        if with_join:
            await join()


@TestFeature
def suites(self, executor, workers=10, with_join=False):
    with executor(workers) as pool:
        kwargs = {"flags": TE, "parallel": True, "executor": pool}
        Suite(name="suite with ThreadPool join=True", test=suite, **kwargs)(
            executor=ThreadPool, with_join=True
        )
        Suite(name="suite with ThreadPool join=False", test=suite, **kwargs)(
            executor=ThreadPool, with_join=False
        )
        Suite(name="suite with ProcessPool join=True", test=suite, **kwargs)(
            executor=ProcessPool, with_join=True
        )
        Suite(name="suite with ProcessPool join=False", test=suite, **kwargs)(
            executor=ProcessPool, with_join=False
        )
        Suite(name="async suite with AsyncPool join=True", test=async_suite, **kwargs)(
            executor=AsyncPool, with_join=True
        )
        Suite(name="async suite with AsyncPool join=False", test=async_suite, **kwargs)(
            executor=AsyncPool, with_join=False
        )
        Suite(name="async suite with ThreadPool join=True", test=async_suite, **kwargs)(
            executor=ThreadPool, with_join=True
        )
        Suite(
            name="async suite with ThreadPool join=False", test=async_suite, **kwargs
        )(executor=ThreadPool, with_join=False)
        Suite(
            name="async suite with ProcessPool join=True", test=async_suite, **kwargs
        )(executor=ProcessPool, with_join=True)
        Suite(
            name="async suite with ProcessPool join=False", test=async_suite, **kwargs
        )(executor=ProcessPool, with_join=False)
        if with_join:
            join()


@TestModule
def feature(self):
    """Check parallel test termination."""
    for i in range(1):
        start_time = time.time()
        r = Suite(
            f"suites executed with ThreadPool join=True #{i}", test=suites, flags=TE
        )(executor=ThreadPool, workers=5, with_join=True)
    # Suite("suites executed with ThreadPool join=False", test=suites, flags=TE)(executor=ThreadPool, with_join=False)


if main():
    feature()
