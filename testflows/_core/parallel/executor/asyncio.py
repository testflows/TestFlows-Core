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
import uuid
import atexit
import weakref
import itertools
import threading
import concurrent.futures.thread as _base

from .future import Future 
from .. import _get_parallel_context
from ..asyncio import is_running_in_event_loop, asyncio
from .. import current, join as parallel_join

_tasks_queues = weakref.WeakKeyDictionary()
_shutdown = False

def _python_exit():
    global _shutdown
    _shutdown = True
    # FIXME: debug leaked
    #import sys
    #import gc
    #for k in (list(_tasks_queues.keys())):
    #    print(f"{k} {sys.getrefcount(k)} {gc.get_referrers(k)}")
    for work_queue in _tasks_queues.values():
        if work_queue._loop.is_running():
            asyncio.run_coroutine_threadsafe(work_queue.put(None), loop=work_queue._loop)
    for task in _tasks_queues.keys():
        task.result()

atexit.register(_python_exit)

class _AsyncWorkItem(_base._WorkItem):
    async def run(self):
        if not self.future.set_running_or_notify_cancel():
            return
        try:
            result = self.fn(*self.args, **self.kwargs)
            if asyncio.iscoroutine(result):
                result = await result
        except BaseException as exc:
            self.future.set_exception(exc)
            self = None
        else:
            self.future.set_result(result)


async def _worker(executor_weakref, work_queue):
    while True:
        try:
            work_item = await work_queue.get()
            try:
                if work_item is not None:
                    await work_item.run()
                    del work_item
                    continue
            finally:
                work_queue.task_done()
        finally:
            executor = executor_weakref()
            try:
                if _shutdown or executor is None or executor._shutdown:
                    if executor is not None:
                        executor._shutdown = True
                    await work_queue.put(None)
                    return
            finally:
                del executor


async def _loop_send_stop_event(stop_event):
    """Set stop event to stop event loop.
    """
    stop_event.set()


async def _loop_main(stop_event):
    """Event loop main function
    that blocks until stop event is set.
    """
    await stop_event.wait()


def _async_loop_thread(loop, stop_event):
    """Async loop thread.
    """
    asyncio.set_event_loop(loop)

    loop.run_until_complete(_loop_main(stop_event))

    tasks = [task for task in asyncio.all_tasks(loop=loop)]
    for task in tasks:
        task.cancel()

    loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
    loop.close()


class AsyncPoolExecutor(_base._base.Executor):
    """Async pool executor.
    """
    _counter = itertools.count().__next__

    def __init__(self, max_workers=1024, task_name_prefix="",
            loop=None, _check_max_workers=True, join_on_shutdown=True):
        if _check_max_workers and int(max_workers) <= 0:
            raise ValueError("max_workers must be greater than 0")
        self._open = False
        self._max_workers = max_workers
        self._loop = loop or asyncio.new_event_loop()
        self._loop_stop_event = asyncio.Event(loop=self._loop)
        self._work_queue = asyncio.Queue(loop=self._loop)
        self._tasks = set()
        self._shutdown = False
        self._shutdown_lock = threading.Lock()
        self._task_name_prefix = (task_name_prefix or
            ("AsyncPoolExecutor-%d" % self._counter()))
        self._async_loop_thread = None
        self._uid = str(uuid.uuid1())
        self._join_on_shutdown = join_on_shutdown

    @property
    def open(self):
        return bool(self._open)

    def __enter__(self):
        with self._shutdown_lock:
            if not self._open:
                self._async_loop_thread = threading.Thread(target=_async_loop_thread,
                    kwargs={"loop": self._loop, "stop_event": self._loop_stop_event},
                    daemon=True)
                self._async_loop_thread.start()
                self._open = True
            return self

    def submit(self, fn, args=None, kwargs=None, block=True):
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}

        with self._shutdown_lock:
            if not self._open:
                raise RuntimeError("cannot schedule new futures before pool is opened")
            if self._shutdown:
                raise RuntimeError("cannot schedule new futures after shutdown")
            if _shutdown:
                raise RuntimeError("cannot schedule new futures after interpreter shutdown")

            future = Future()
            future._executor_uid = self._uid

            ctx = _get_parallel_context()
            args = fn, *args
            work_item = _AsyncWorkItem(future, ctx.run, args, kwargs)

            idle_workers = self._adjust_task_count()

            if (idle_workers or block) and self._max_workers > 0:
                if is_running_in_event_loop() and asyncio.get_event_loop() is self._loop:
                    raise RuntimeError("deadlock detected")
                asyncio.run_coroutine_threadsafe(self._work_queue.put(work_item), loop=self._loop).result()

        if (not block and not idle_workers) or self._max_workers < 1:
            if is_running_in_event_loop() and asyncio.get_event_loop() is self._loop:
                raise RuntimeError("deadlock detected")
            asyncio.run_coroutine_threadsafe(work_item.run(), loop=self._loop).result()

        return future

    def _adjust_task_count(self):
        """Increase worker count up to max_workers if needed.
        Returns `True` if worker is immediately available
        to handle the work item or `False` otherwise.
        """
        if len(self._tasks) - self._work_queue._unfinished_tasks > 0:
            return True

        def weakref_cb(_, work_queue=self._work_queue):
            asyncio.run_coroutine_threadsafe(work_queue.put(None), loop=self._loop).result()

        num_tasks = len(self._tasks)
        if num_tasks < self._max_workers:
            task_name = "%s_%d" % (self._task_name_prefix or self, num_tasks)
            task = asyncio.run_coroutine_threadsafe(_worker(weakref.ref(self, weakref_cb), self._work_queue), loop=self._loop)
            self._tasks.add(task)
            _tasks_queues[task] = self._work_queue
            return True

        return False

    def shutdown(self, wait=True, test=None):
        with self._shutdown_lock:
            if self._shutdown:
                return
            self._shutdown = True
            if not self._loop.is_running():
                return
            asyncio.run_coroutine_threadsafe(
                self._work_queue.put(None), loop=self._loop).result()

        if wait:
            if test is None:
                test = current()
            try:
                if test:
                    if self._join_on_shutdown:
                        parallel_join(no_async=True, test=test, filter=lambda future: hasattr(future, "_executor_uid") and future._executor_uid == self._uid, cancel_pending=True)
            finally:
                exc = None
                for task in self._tasks:
                    try:
                        task.result()
                    except BaseException as e:
                        exc = e
                try:
                    if exc is not None:
                        raise exc
                finally:
                    asyncio.run_coroutine_threadsafe(
                            _loop_send_stop_event(self._loop_stop_event), loop=self._loop
                        ).result()
                    if self._async_loop_thread is not None:
                        self._async_loop_thread.join()


class SharedAsyncPoolExecutor(AsyncPoolExecutor):
    """Shared async pool executor.
    """
    def __init__(self, max_workers, task_name_prefix="", join_on_shutdown=True):
        self.initargs = (max_workers, task_name_prefix, join_on_shutdown) 

        if int(max_workers) < 0:
            raise ValueError("max_workers must be positive or 0")
        super(SharedAsyncPoolExecutor, self).__init__(
            max_workers=max_workers-1, task_name_prefix=task_name_prefix,
            _check_max_workers=False, join_on_shutdown=join_on_shutdown)

    def submit(self, fn, args=None, kwargs=None, block=False):
        return super(SharedAsyncPoolExecutor, self).submit(fn=fn, args=args, kwargs=kwargs, block=block)


GlobalAsyncPoolExecutor = SharedAsyncPoolExecutor
