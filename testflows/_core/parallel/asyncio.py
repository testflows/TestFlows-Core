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
import inspect
import asyncio
from asyncio import *

async def async_await(coroutine):
    r = coroutine
    while inspect.isawaitable(r):
        r = await r
    return r

async def async_next(async_iterator):
    return await async_iterator.__anext__()

def is_running_in_event_loop():
    """Check if running in async event loop.
    """
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        pass
    return False
