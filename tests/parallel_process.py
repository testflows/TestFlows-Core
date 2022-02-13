from multiprocessing.managers import ValueProxy
import os
import sys
import time
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
def my_scenario(self, count=1, sleep=0):
    """Simple scenario with 0 or more steps.
    """
    for i in range(1):
        note(f"hello {os.getpid()}")
    for i in range(count):
        with Step(f"hello there {i} - {self.name}"):
            time.sleep(sleep)
    return "value"


def func_with_scenario():
    """Simple function that runs a scenario.
    """
    Scenario(test=my_scenario)()


def func_with_inline_scenario():
    """Simple function that runs inline scenario.
    """
    with Scenario("my test") as test:
        note(f"hi from test {test.name}")


def simple(x, y):
    """Simple function.
    """
    print("foo", file=sys.stdout)
    print("boo", file=sys.stderr)
    for i in range(1):
        note(f"here {os.getpid()}")
    return x + y

def simple_error():
    """Simple function that raises error.
    """
    raise ValueError("error")


@TestFeature
def feature(self):
    """Test running tests in parallel processes.
    """
    with Scenario("try using process pool"):
        with ProcessPool() as pool:
            pass

    with Scenario("run simple function in process pool"):
        with ProcessPool() as pool:
            with Example("single"):
                for i in range(1):
                    f = pool.submit(simple, args=[2,2])
                    r = f.result()
                    assert r == 4, error()

            with Example("multiple"):
                tasks = []
                for i in range(10):
                    tasks.append(pool.submit(simple, kwargs={"x":2,"y":2}))
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

    # with Scenario("run decorated tests in parallel"):
    #     with ProcessPool() as pool:
    #         futures = []
    #         for i in range(10):
    #             futures.append(
    #                     Scenario(name=f"test {i}", test=my_scenario, parallel=True, executor=pool)()
    #                 )
    #         for v in join(*futures):
    #             v = v.result.value
    #             assert v == "value", error()

#           with Scenario("booo"):
#               for i in range(2):
#                   f = Scenario(name=f"test {i}", test=my_test, parallel=True, flags=TE)()#, executor=pool)()
#               fail("failing")
#           #for i in range(1):
#           #    f = pool.submit(fn, args=[my_test])
#           #f.result()


if main():
    feature()

