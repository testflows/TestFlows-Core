# Copyright 2021 Katteli Inc.
# TestFlows.com Open-Source Software Testing Framework (http://testflows.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# to the end flag
import asyncio
import contextvars
from collections import namedtuple
from concurrent.futures import CancelledError
from concurrent.futures import TimeoutError
from concurrent.futures import Future as ConcurrentFuture
from .asyncio import Future as AsyncFuture
from .asyncio import is_running_in_event_loop
from .asyncio import TimeoutError as AsyncTimeoutError
from .asyncio import CancelledError as AsyncCancelledError

def Context(**kwargs):
    """Convenience function to create
    a namedtuple to store parallel context variables.
    """
    return namedtuple("ParallelContext", " ".join(kwargs.keys()))(*kwargs.values())

context = Context(
    current=contextvars.ContextVar('_testflows_current', default=None),
    previous=contextvars.ContextVar('_testflows_previous', default=None),
    top=contextvars.ContextVar('_testflows_top', default=None),
    is_valid=contextvars.ContextVar('_testflows_is_valid', default=None),
)

# set current parallel context as valid
context.is_valid.set(True)

ContextVar = contextvars.ContextVar
copy_context = contextvars.copy_context

def convert_result_to_concurrent_future(fn, args=None, kwargs=None):
    """Make concurrent future out of result of a function call.
    """
    if args is None:
        args = ()
    if kwargs is None:
        kwargs = {}

    future = ConcurrentFuture()
    future.set_running_or_notify_cancel()
    try:
        future.set_result(fn(*args, **kwargs))
    except BaseException as exc:
        future.set_exception(exc)

    return future

def _get_parallel_context():
    """Return parallel context based on contextvars
    with all the user context variables cleared
    to None.
    """
    ctx = contextvars.copy_context()
    # clear any user context variables to None
    for var in ctx.keys():
        if not var.name.startswith("_testflows_"):
            # in Python 3.8 ContextVar can't be cleared
            # and therefore the best we can do is to set
            # user context variable to None
            var.set(None)
    return ctx

def _check_parallel_context():
    """Check if parallel parallel context is valid.
    """
    if not context.is_valid.get():
        raise RuntimeError("parallel context was not set")

def top(value=None):
    """Highest level test.
    """
    if value is not None:
        context.top.set(value)
    return context.top.get()

def current(value=None, set_value=False):
    """Currently executing test.
    """
    if value is not None or set_value:
        context.current.set(value)
    return context.current.get()

def previous(value=None):
    """Last executed test.
    """
    if value is not None:
        context.previous.set(value)
    return context.previous.get()

def join(*futures, cancel=None, test=None, raise_exception=True):
    """Wait for parallel tests to complete. Returns a list of
    completed tests. If any of the parallel tests raise an exception then
    the first exception is raised.

    If raise_exception is False then no exception is raised
    and a (tests, exceptions) tuple is returned.

    :param cancel: cancel any pending parallel tests
    :param test: current test
    :param raise_exception: raise first exception, default: True.
    """
    if is_running_in_event_loop():
        return _async_join(*futures, cancel=cancel, test=test, raise_exception=raise_exception)

    if test is None:
        test = current()
    top_test = top()

    futures = list(futures) or test.futures
    exceptions = []
    tests = []

    while True:
        if not futures:
            break
        future = futures.pop()

        if not isinstance(future, ConcurrentFuture):
            continue

        try:
            if cancel or len(exceptions) > 0 or test.terminating is not None or top_test.terminating is not None:
                future.cancel()
            try:
                exception = future.exception(timeout=1)
                if exception is not None:
                    exceptions.append(exception)
                else:
                    tests.append(future.result())
            except TimeoutError:
                futures.append(future)
                continue
        except CancelledError:
            pass

    if raise_exception is False:
        return tests, exceptions
    else:
        if exceptions:
            raise exceptions[0]
        return tests

async def _async_join(*futures, cancel=None, test=None, raise_exception=True):
    """Wait for parallel async tests to complete. Returns a list of
    completed tests. If any of the parallel tests raise an exception then
    the first exception is raised.

    If raise_exception is False then no exception is raised
    and a (tests, exceptions) tuple is returned.

    :param cancel: cancel any pending parallel tests
    :param test: current test
    :param raise_exception: raise first exception, default: True.
    """
    if test is None:
        test = current()
    top_test = top()

    futures = list(futures) or test.futures
    exceptions = []
    tests = []

    while True:
        if not futures:
            break
        future = futures.pop()

        if isinstance(future, ConcurrentFuture):
            future = asyncio.wrap_future(future)

        if not isinstance(future, AsyncFuture):
            continue

        try:
            if cancel or len(exceptions) > 0 or test.terminating is not None or top_test.terminating is not None:
                future.cancel()
            try:
                await asyncio.wait_for(asyncio.shield(future), timeout=1)
                exception = future.exception()
                if exception is not None:
                    exceptions.append(exception)
                else:
                    tests.append(future.result())
            except AsyncTimeoutError:
                futures.append(future)
                continue
        except AsyncCancelledError:
            pass

    if raise_exception is False:
        return tests, exceptions
    else:
        if exceptions:
            raise exceptions[0]
        return tests
