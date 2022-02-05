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
import sys
import atexit
import inspect
import weakref
import queue
import threading
import traceback
import itertools
import textwrap
import subprocess
import concurrent.futures._base as _base

import testflows.settings as settings

from .future import Future

from ..asyncio import is_running_in_event_loop, wrap_future
from ..service import ServiceObjectType, process_service, auto_expose
from .. import current, top, previous, _get_parallel_context

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


WorkQueueType = ServiceObjectType("WorkQueue", auto_expose(queue.Queue()))

ProcessError = subprocess.SubprocessError

class _WorkItem(object):
    def __init__(self, write_logfile, read_logfile, current_test, previous_test, top_test, future, fn, args, kwargs):
        self.write_logfile = write_logfile
        self.read_logfile = read_logfile
        self.current_test = current_test
        self.previous_test = previous_test
        self.top_test = top_test
        self.future = future
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        if not self.future.set_running_or_notify_cancel():
            return

        ctx = _get_parallel_context()
        
        def runner(self):
            import testflows.settings as settings

            try:
                top(self.top_test)
                previous(self.previous_test)
                current(self.current_test)
                settings.write_logfile = self.write_logfile
                settings.read_logfile = self.read_logfile

                result = self.fn(*self.args, **self.kwargs)
            except BaseException:
                exc_type, exc_value, exc_tb = sys.exc_info()
                exc = exc_type(str(exc_value) + "\n\nWorker Traceback (most recent call last):\n" + "".join(traceback.format_tb(exc_tb)).rstrip())
                self.future.set_exception(exc)
                # Break a reference cycle with the exception 'exc'
                self = None
            else:
                try:
                    self.future.set_result(result)
                except TypeError:
                    self.future.set_result(process_service().register(result))

        ctx.run(runner, self)


class ProcessPoolExecutor(_base.Executor):
    """Process pool executor.
    """
    _counter = itertools.count().__next__

    def __init__(self, max_workers=16, process_name_prefix="", _check_max_workers=True):
        if _check_max_workers and int(max_workers) <= 0:
            raise ValueError("max_workers must be greater than 0")
        self._open = False
        self._max_workers = max_workers
        self._raw_work_queue = queue.Queue()
        self._work_queue = process_service().register(self._raw_work_queue)
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

            service = process_service()

            future = service.register(Future())

            current_test = service.register(current())
            previous_test = service.register(previous())
            top_test = service.register(top())
            write_logfile = service.register(current().io.io.io.writer)
            read_logfile = service.register(current().io.io.io.reader)

            work_item = _WorkItem(write_logfile, read_logfile, current_test, previous_test, top_test, future, fn, args, kwargs)

            idle_workers = self._adjust_process_count()

            if (idle_workers or block) and self._max_workers > 0:
                self._raw_work_queue.put(work_item)

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
        if len(self._processes) - self._raw_work_queue.unfinished_tasks > 0:
            return True

        num_procs = len(self._processes)

        if num_procs < self._max_workers:
            command = ["tfs-worker",
                "--oid", str(self._work_queue.oid),
                "--hostname", str(self._work_queue.hostname),
                "--port", str(self._work_queue.port)
            ]

            if settings.debug:
                command.append("--debug")
            if settings.no_colors:
                command.append("--no-colors")

            proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc.stdout.readline()
            if proc.poll() is not None:
                returncode, err = proc.returncode, textwrap.indent(proc.stderr.read().decode('utf-8'), prefix='  ')
                raise ProcessError(f"failed to start worker process {proc.pid} return code {returncode}\n{err}")
            self._processes.add(proc)
            _process_queues[proc] = self._raw_work_queue
            return True

        return False

    def shutdown(self, wait=True):
        with self._shutdown_lock:
            if self._shutdown:
                return
            self._shutdown = True

            for proc in self._processes:
                self._raw_work_queue.put_nowait(None)

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
