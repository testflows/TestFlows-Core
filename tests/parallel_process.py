from multiprocessing.managers import ValueProxy
import os
import sys
import time
import asyncio

from tracemalloc import start

from testflows.core import *
from testflows.asserts import error, raises

from testflows._core.parallel.service import BaseServiceObject, ServiceError
from testflows._core.exceptions import exception as get_exception


@TestStep(Given)
def start_process_service(self):
    with process_service() as service:
        yield service


@TestScenario
def my_scenario(self, count=1, sleep=0, force_fail=False):
    """Simple scenario with 0 or more steps."""
    for i in range(1):
        note(f"hello {os.getpid()}")
    for i in range(count):
        with Step(f"hello there {i} - {self.name}"):
            time.sleep(sleep)
            if force_fail:
                fail("forced fail")
    return "value"


def func_with_scenario():
    """Simple function that runs a scenario."""
    Scenario(test=my_scenario)()


def func_with_inline_scenario():
    """Simple function that runs inline scenario."""
    with Scenario("my test") as test:
        note(f"hi from test {test.name}")


def simple(x, y):
    """Simple function."""
    print("foo", file=sys.stdout)
    print("boo", file=sys.stderr)
    for i in range(1):
        note(f"here {os.getpid()}")
    return x + y


def simple_error():
    """Simple function that raises error."""
    raise ValueError("error")


@TestScenario
async def simple_async_test(self):
    note(f"hello {self.name} {os.getpid()}")


@TestScenario
async def my_async_test(self):
    with ProcessPool() as pool:
        f = Scenario(name=f"test 0", test=my_scenario, parallel=True, executor=pool)()
        assert isinstance(f, asyncio.Future), error()
        r = await f
        assert r.value == "value", error()

        r = await Scenario(
            name=f"test 1", test=my_scenario, flags=XFAIL, parallel=True, executor=pool
        )(force_fail=True)
        assert isinstance(r, XFail), error()

        async with Scenario("multiple parallel tests"):
            for i in range(10):
                Scenario(
                    name=f"test {i}",
                    test=my_scenario,
                    flags=XFAIL,
                    parallel=True,
                    executor=pool,
                )()
            await join()

        # async with Scenario("multiple parallel async tests"):
        #    for i in range(10):
        #        Scenario(name=f"test {i}", test=simple_async_test, flags=XFAIL, parallel=True, executor=pool)()
        #    await join()


@TestFeature
def feature(self):
    """Test running tests in parallel processes."""
    with Scenario("try using process pool"):
        with ProcessPool() as pool:
            pass

    with Scenario("run simple function in process pool"):
        with ProcessPool() as pool:
            with Example("single"):
                for i in range(1):
                    f = pool.submit(simple, args=[2, 2])
                    r = f.result()
                    assert r == 4, error()
            for i in range(3):
                with Example(f"multiple {i}"):
                    tasks = []
                    for i in range(10):
                        tasks.append(pool.submit(simple, kwargs={"x": 2, "y": 2}))
                    for task in tasks:
                        r = task.result()
                        assert r == 4, error()

            with Example("raises exception"):
                f = pool.submit(simple_error)
                with raises(ValueError):
                    f.result()

            with Example("call with wrong number of arguments"):
                f = pool.submit(simple, args=[2])
                with raises(TypeError):
                    f.result()

            with Example("use non function"):
                f = pool.submit(None)
                with raises(TypeError):
                    f.result()

    with Scenario("run decorated tests in parallel"):
        with ProcessPool() as pool:
            with Scenario("multiple tests"):
                futures = []
                for i in range(10):
                    futures.append(
                        Scenario(
                            name=f"test {i}",
                            test=my_scenario,
                            parallel=True,
                            executor=pool,
                        )()
                    )
                for v in join(*futures):
                    v = v.value
                    assert v == "value", error()

            with Scenario("check child count is being incremented") as test:
                count = test.child_count
                debug(f"before: {test.child_count}")
                futures = []
                for i in range(2):
                    futures.append(
                        Scenario(
                            name=f"my test {i}",
                            test=my_scenario,
                            parallel=True,
                            executor=pool,
                        )()
                    )
                join(*futures)
                debug(f"after: {test.child_count}")
                assert test.child_count == count + 2, error()

            with Scenario("failing parallel test"):
                Scenario(
                    name=f"test",
                    test=my_scenario,
                    parallel=True,
                    flags=XFAIL,
                    executor=pool,
                )(force_fail=True).result()

            with Scenario("check if parallel test future is added to futures") as test:
                f1 = Scenario(
                    name=f"test 0",
                    test=my_scenario,
                    parallel=True,
                    flags=XFAIL,
                    executor=pool,
                )()
                f2 = Scenario(
                    name=f"test 1",
                    test=my_scenario,
                    parallel=True,
                    flags=XFAIL,
                    executor=pool,
                )()
                assert len(test.futures) == 2, error()
                join(f1)
                join(f2)
                join()
                assert len(test.futures) == 0, error()

        with Scenario("async test that runs parallel tests in a process pool"):
            Scenario(test=my_async_test)()


if main():
    feature()
