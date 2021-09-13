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
import queue
import weakref
import threading
import concurrent.futures.thread as _base

from .. import _get_parallel_context
from ..asyncio import is_running_in_event_loop, wrap_future

def _worker(executor_weakref, work_queue):
    try:
        while True:
            work_item = work_queue.get(block=True)
            try:
                if work_item is not None:
                    work_item.run()
                    del work_item
                    continue
            finally:
                work_queue.task_done()

            executor = executor_weakref()
            try:
                if _base._shutdown or executor is None or executor._shutdown:
                    if executor is not None:
                        executor._shutdown = True
                    work_queue.put(None)
                    return
            finally:
                del executor
    except BaseException:
        _base.LOGGER.critical('Exception in thread worker', exc_info=True)


class ThreadPoolExecutor(_base.ThreadPoolExecutor):
    """Thread pool executor.
    """
    def __init__(self, max_workers=16, thread_name_prefix="", _check_max_workers=True):
        if _check_max_workers and int(max_workers) <= 0:
            raise ValueError("max_workers must be greater than 0")
        self._open = False
        self._max_workers = max_workers
        self._work_queue = queue.Queue()
        self._threads = set()
        self._broken = False
        self._shutdown = False
        self._shutdown_lock = threading.Lock()
        self._thread_name_prefix = (thread_name_prefix or
                ("ThreadPoolExecutor-%d" % self._counter()))

    @property
    def open(self):
        """Return if pool is opened.
        """
        return bool(self._open)

    def __enter__(self):
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
            if _base._shutdown:
                raise RuntimeError("cannot schedule new futures after "
                    "interpreter shutdown")

            future = _base._base.Future()
            ctx = _get_parallel_context()
            args = fn, *args
            work_item = _base._WorkItem(future, ctx.run, args, kwargs)

            idle_workers = self._adjust_thread_count()

            if (idle_workers or block) and self._max_workers > 0:
                self._work_queue.put(work_item)

        if (not block and not idle_workers) or self._max_workers < 1:
            work_item.run()

        if is_running_in_event_loop():
            return wrap_future(future)

        return future

    def _adjust_thread_count(self):
        """Increase worker count up to max_workers if needed.
        Return `True` if worker is immediately available to handle
        the work item or `False` otherwise.
        """
        if len(self._threads) - self._work_queue.unfinished_tasks > 0:
            return True

        def weakref_cb(_, work_queue=self._work_queue):
            work_queue.put(None)

        num_threads = len(self._threads)
        if num_threads < self._max_workers:
            thread_name = "%s_%d" % (self._thread_name_prefix or self, num_threads)
            thread = threading.Thread(name=thread_name,
                target=_worker, args=(weakref.ref(self, weakref_cb),
                self._work_queue), daemon=True)
            thread.start()
            self._threads.add(thread)
            _base._threads_queues[thread] = self._work_queue
            return True

        return False

    def shutdown(self, wait=True):
        with self._shutdown_lock:
            if self._shutdown:
                return
            self._shutdown = True
            self._work_queue.put(None)
        if wait:
            for thread in self._threads:
                thread.join()


class SharedThreadPoolExecutor(ThreadPoolExecutor):
    """Shared thread pool executor.
    """
    def __init__(self, max_workers, thread_name_prefix=""):
        if int(max_workers) < 0:
            raise ValueError("max_workers must be positive or 0")
        super(SharedThreadPoolExecutor, self).__init__(
            max_workers=max_workers-1, thread_name_prefix=thread_name_prefix, _check_max_workers=False)

    def submit(self, fn, args=None, kwargs=None, block=False):
        return super(SharedThreadPoolExecutor, self).submit(fn=fn, args=args, kwargs=kwargs, block=block)


GlobalThreadPoolExecutor = SharedThreadPoolExecutor
