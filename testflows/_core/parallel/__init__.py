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
import contextvars

from collections import namedtuple

from concurrent.futures import CancelledError
from concurrent.futures import TimeoutError
from concurrent.futures import Future as ConcurrentFuture

from .asyncio import asyncio, wrap_future, OptionalFuture
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

def join(*future, futures=None, test=None, filter=None, all=False, no_async=False, cancel_pending=False):
    """Wait for parallel test futures to complete.
    Returns a list of completed tests.
    
    Terminates current test if any of the parallel
    tests raise an exception.

    If no futures specified uses test.futures().
    If test is not specified test is set to current().

    :param *future: one or more futures (optional)
    :param futures: list of futures (optional)
    :param test: current test, default: current()
    :param filter: filter function, default: None
    :param all: wait and join all the tests, default: False
    :param no_async: force non async join while running in event loop
    :param cancel_pending: cancel any pending futures
    """
    if no_async is False and is_running_in_event_loop():
        return _async_join(*future, futures=futures, test=test, filter=filter, all=all, cancel_pending=cancel_pending)

    if test is None:
        test = current()

    futures = list(future) or futures or test.futures
    tests = []
    exception = None
    filtered_count = 0

    while True:
        if not futures or filtered_count >= len(futures):
            break

        future = None
        try:
            future = futures.pop(0)

            if filter and not filter(future):
                futures.append(future)
                filtered_count += 1
                continue

            filtered_count = 0

            if cancel_pending:
                if future.cancel():
                    continue
            try:
                exc = future.exception(timeout=0.1)
                if exc is not None:
                    if exception is None:
                        exception = exc
                        cancel_pending = True
                        if test:
                            test.terminate()
                    if not all:
                        raise exception
                else:
                    tests.append(future.result(timeout=0.1))
            except CancelledError:
                continue
            except TimeoutError:
                futures.append(future)
                continue
        except BaseException:
            if future is not None:
                futures.append(future)
            raise

    if exception is not None:
        raise exception
    return tests

async def _async_join(*future, futures=None, test=None, filter=None, all=False, cancel_pending=False):
    """Wait for async parallel test futures to complete.
    Returns a list of completed tests.
    
    Terminates current test if any of the parallel
    tests raise an exception.

    If no futures specified uses test.futures().
    If test is not specified test is set to current().

    :param *future: one or more futures (optional)
    :param futures: list of futures (optional)
    :param test: current test, default: current()
    :param filter: filter function, default: None
    :param all: wait and join all the tests, default: False
    :param cancel_pending: cancel any pending futures
    """
    if test is None:
        test = current()

    futures = list(future) or futures or test.futures
    tests = []
    exception = None
    filtered_count = 0

    while True:
        if not futures or filtered_count >= len(futures):
            break

        future = None
        try:
            future = futures.pop(0)

            if filter and not filter(future):
                futures.append(future)
                filtered_count += 1
                continue

            filtered_count = 0

            try:
                f = future
                if isinstance(future, ConcurrentFuture):
                    f = wrap_future(future, new_future=OptionalFuture())

                if cancel_pending:
                    if future.cancel():
                        continue

                tests.append(await asyncio.wait_for(asyncio.shield(f), timeout=0.1))
            except AsyncCancelledError:
                continue
            except AsyncTimeoutError:
                futures.append(future)
                continue
        except BaseException as exc:
            if future is not None:
                if future.done():
                    if test:
                        test.terminate()
                    if not all:
                        raise
                    if exception is None:
                        exception = exc
                        cancel_pending = True
                    continue
                else:
                    futures.append(future)
            raise

    if exception is not None:
        raise exception
    return tests
