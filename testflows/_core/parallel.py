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
from concurrent.futures import Future
from concurrent.futures.thread import ThreadPoolExecutor as _PythonThreadPoolExecutor

def Context(**kwargs):
    """Convenience function to create
    a namedtuple to store parallel context variables.
    """
    return namedtuple("ParallelContext", " ".join(kwargs.keys()))(*kwargs.values())

context = Context(
    current=contextvars.ContextVar('_tfs_current', default=None),
    previous=contextvars.ContextVar('_tfs_previous', default=None),
    top=contextvars.ContextVar('_tfs_top', default=None),
    is_valid=contextvars.ContextVar('_tfs_is_valid', default=None),
)

# set current parallel context as valid
context.is_valid.set(True)

ContextVar = contextvars.ContextVar
copy_context = contextvars.copy_context

class Pool(_PythonThreadPoolExecutor):
    """Parallel thread pool.
    """
    def __init__(self, *args, **kwargs):
        self.open = False
        self.parallel_tests = {}
        super(Pool, self).__init__(*args, **kwargs)

    def __enter__(self):
        r = super(Pool, self).__enter__()
        self.open = True
        return r

    def submit(self, fn, *args, **kwargs):
        ctx = contextvars.copy_context()

        # clear any user context variables to None
        for var in ctx.keys():
            if not var.name.startswith("_tfs"):
                # in Python 3.8 ContextVar can't be cleared
                # and therefore the best we can do is to set
                # user context variable to None
                var.set(None)

        if not self.open:
            raise RuntimeError("parallel pool is not opened. Use `with` statement to open the pool.")
        if self._shutdown:
            raise RuntimeError("parallel pool can't be used after shutdown")
        return super(Pool, self).submit(ctx.run, fn, *args, **kwargs)

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
        if not isinstance(future, Future):
            continue
        try:
            if cancel or len(exceptions) > 0 or test.terminating is not None or top_test.terminating is not None:
                future.cancel()
            try:
                exception = future.exception(timeout=1)
                if exception is not None:
                    exceptions.append(exception)
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
