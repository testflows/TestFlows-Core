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
import time
import asyncio
import threading

if sys.platform == "win32":
    _loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
else:
    _loop = asyncio.get_event_loop()


threading.Thread(target=_loop.run_forever, daemon=True).start()

def stop():
    """Cleanly stop event loop.
    """
    _loop.call_soon_threadsafe(_loop.stop)

    while _loop.is_running():
        time.sleep(0.1)

def async_call(awaitable, sync=True, loop=None):
    """Run async awaitable object.
    """
    if loop is None:
        loop = _loop

    future = asyncio.run_coroutine_threadsafe(awaitable, loop)

    if sync is False:
        return future

    return future.result()
