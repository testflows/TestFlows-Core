# Copyright 2022 Katteli Inc.
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
import os
import atexit
import inspect
import weakref
import queue
import threading
import itertools
import subprocess
import concurrent.futures._base as _base

from .future import Future

from .. import _get_parallel_context
from ..asyncio import is_running_in_event_loop, wrap_future
from ..service import ServiceObjectType, process_service

_process_queues = weakref.WeakKeyDictionary()
_shutdown = False

def _python_exit():
    global _shutdown
    _shutdown = True
    items = list(_process_queues.items())
    for proc, _ in items:
        proc.terminate()
    for proc, _ in items:
        proc.wait()

atexit.register(_python_exit)


WorkQueueType = ServiceObjectType("WorkQueue", inspect.getmembers(queue.Queue()))

class _WorkItem(object):
    def __init__(self, future, fn, args, kwargs):
        self.future = future
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        if not self.future.set_running_or_notify_cancel():
            return

        try:
            result = self.fn(*self.args, **self.kwargs)
        except BaseException as exc:
            self.future.set_exception(exc)
            # Break a reference cycle with the exception 'exc'
            self = None
        else:
            self.future.set_result(result)


class ProcessPoolExecutor(_base.Executor):
    """Process pool executor.
    """
    _counter = itertools.count().__next__

    def __init__(self, max_workers=16, process_name_prefix="", _check_max_workers=True):
        if _check_max_workers and int(max_workers) <= 0:
            raise ValueError("max_workers must be greater than 0")
        self._open = False
        self._max_workers = max_workers
        self._work_queue = process_service().register(queue.Queue())
        self._processes = set()
        self._broken = False
        self._shutdown = False
        self._shutdown_lock = threading.Lock()
        self._process_name_prefix = f"{process_name_prefix}ProcessPoolExecutor-{os.getpid()}-{self._counter()}"

    @property
    def open(self):
        """Return if pool is opened.
        """
        return bool(self._open)

    def __enter__(self):
        self._open = True
        return self

    def map(self, fn, *iterables, timeout=None, chunksize=1):
        raise NotImplementedError()

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
                raise RuntimeError("cannot schedule new futures after "
                    "interpreter shutdown")

            future = process_service().register(Future())

            # FIXME: need to handle context
            #ctx = _get_parallel_context() 
            #args = fn, *args
            
            work_item = _WorkItem(future, fn, args, kwargs)

            idle_workers = self._adjust_process_count()

            if (idle_workers or block) and self._max_workers > 0:
                self._work_queue.put(work_item)

        if (not block and not idle_workers) or self._max_workers < 1:
            work_item.run()

        if is_running_in_event_loop():
            return wrap_future(future)

        return future

    def _adjust_process_count(self):
        """Increase worker count up to max_workers if needed.
        Return `True` if worker is immediately available to handle
        the work item or `False` otherwise.
        """
        if len(self._processes) - self._work_queue.unfinished_tasks > 0:
            return True

        num_procs = len(self._processes)

        if num_procs < self._max_workers:
            proc = subprocess.Popen(["tfs-worker",
                    "--oid", str(self._work_queue.oid),
                    "--hostname", str(self._work_queue.hostname),
                    "--port", str(self._work_queue.port)
                ])
            self._processes.add(proc)
            _process_queues[proc] = self._work_queue
            return True

        return False

    def shutdown(self, wait=True):
        with self._shutdown_lock:
            if self._shutdown:
                return
            self._shutdown = True

            for proc in self._processes:
                self._work_queue.put_nowait(None)

        if wait:
            for proc in self._processes:
                proc.wait()


class SharedProcessPoolExecutor(ProcessPoolExecutor):
    """Shared process pool executor.
    """
    def __init__(self, max_workers, process_name_prefix=""):
        if int(max_workers) < 0:
            raise ValueError("max_workers must be positive or 0")
        super(SharedProcessPoolExecutor, self).__init__(
            max_workers=max_workers-1, process_name_prefix=process_name_prefix, _check_max_workers=False)

    def submit(self, fn, args=None, kwargs=None, block=False):
        return super(SharedProcessPoolExecutor, self).submit(fn=fn, args=args, kwargs=kwargs, block=block)


GlobalProcessPoolExecutor = SharedProcessPoolExecutor
