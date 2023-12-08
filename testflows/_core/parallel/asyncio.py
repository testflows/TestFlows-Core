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
import sys
import inspect
import asyncio
import concurrent

from asyncio import *


main_event_loop = None


if main_event_loop is None:
    loop = asyncio.get_event_loop()
    main_event_loop = loop


async def async_await(coroutine):
    r = coroutine
    while inspect.isawaitable(r):
        r = await r
    return r


async def async_next(async_iterator):
    return await async_iterator.__anext__()


def is_running_in_event_loop():
    """Check if running in async event loop."""
    try:
        loop = asyncio.get_running_loop()
        if loop is main_event_loop:
            # don't consider a main event loop (if present)
            # as an event loop where we expect all tests to be async
            return False
        return True
    except RuntimeError:
        pass
    return False


class LoopMixin:
    def __init__(self, *args, loop=None, **kwargs):
        self._loop_mixin = loop
        if sys.version_info < (3, 10, 0):
            kwargs["loop"] = self._loop_mixin
        super(LoopMixin, self).__init__(*args, **kwargs)

    def _get_loop(self):
        if self._loop_mixin is not None:
            return self._loop_mixin
        if sys.version_info >= (3, 10, 0):
            return super(LoopMixin, self)._get_loop()
        return self._loop


class Future(LoopMixin, asyncio.Future):
    pass


class OptionalFuture(Future):
    """Future that will not complain about any
    exceptions not being retrieved.
    """

    def __del__(self):
        return


def wrap_future(future, *, loop=None, new_future=None):
    """Wrap concurrent.futures.Future object."""
    if isfuture(future):
        return future
    assert isinstance(
        future, concurrent.futures.Future
    ), f"concurrent.futures.Future is expected, got {future!r}"
    if loop is None:
        loop = asyncio.events.get_event_loop()
    if new_future is None:
        new_future = loop.create_future()
    asyncio.futures._chain_future(future, new_future)
    return new_future


class Event(LoopMixin, asyncio.Event):
    pass


class Queue(LoopMixin, asyncio.Queue):
    pass


class Lock(LoopMixin, asyncio.Lock):
    pass
