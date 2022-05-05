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
import os
import sys
import json
import time
import uuid
import atexit
import logging
import logging.handlers
import platform
import threading
import contextlib
import multiprocessing
import multiprocessing.managers

import testflows.settings as settings

from queue import Queue, Empty as EmptyQueue
from logging import *

def uid():
    """Get unique id.
    """
    return str(uuid.uuid1())

class Action:
    START = "start"
    END = "end"

class LoggerAdapter(LoggerAdapter):
    """Logger adapter that preserves message extra.
    """
    def process(self, msg, kwargs):
        kwargs_extra = kwargs.get("extra", {})
        kwargs["extra"] = dict(self.extra)
        kwargs["extra"].update(kwargs_extra)
        return msg, kwargs

@contextlib.contextmanager
def Event(tracer, name, source=None, event_id=None):
    if event_id is None:
        event_id = uid()
    
    event_tracer = EventAdapter(tracer, name, source=source, event_id=event_id)
    try:
        event_tracer.debug(f"start", extra={"event_action": Action.START})
        yield event_tracer
    except BaseException as exc:
        event_tracer.exception(exc)
        raise
    finally:
        event_tracer.debug(f"end", extra={"event_action": Action.END})

def EventAdapter(tracer, name, source=None, event_id=None):
    """Event adapter.
    """
    if event_id is None:
        event_id = uid()

    if hasattr(tracer, "extra") and tracer.extra.get("event_name"):
        if name:
            name = f"{tracer.extra['event_name']}.{name}"
        else:
            name = tracer.extra['event_name']
    
    if hasattr(tracer, "extra") and tracer.extra.get("event_source"):
        if source:
            source = f"{tracer.extra['event_source']}.{source}"
        else:
            source = tracer.extra['event_source']

    return LoggerAdapter(tracer, {"event_id": event_id, "event_name": name, "event_source": source})

def TestAdapter(tracer, test):
    """Test adapter.
    """
    return LoggerAdapter(tracer, {"test": test.name, "test_id": test.id_str})

class JSONFormatter(logging.Formatter):
    """JSON formatter.
    """
    def __init__(self, *args, indent=None, **kwargs):
        self.indent = indent
        super(JSONFormatter, self).__init__(*args, **kwargs)

    def format(self, record):
        return json.dumps({k:v for k,v in record.__dict__.items() if k not in ("msg",)}, indent=self.indent, sort_keys=True)

class TestFilter(logging.Filter):
    """Test filter.
    """
    def __init__(self, test, *args, **kwargs):
        self.test = test.name
        self.test_id = test.id_str
        super(TestFilter, self).__init__(*args, **kwargs)

    def filter(self, record):
        """Filter that adds extra fields to each log record.
        """
        record.test = self.test
        record.test_id = self.test_id
        return True

class RecordFilter(logging.Filter):
    """Record filter.
    """
    def __init__(self, *args, **kwargs):
        self.hostname = platform.node()
        self.pid = os.getpid()
        self.process_name = multiprocessing.current_process().name
        self.process_command = " ".join(sys.argv)
        self.time = time.time
        self.thread_ident =  threading.get_ident
        self.thread = threading.current_thread

        super(RecordFilter, self).__init__(*args, **kwargs)

    def filter(self, record):
        """Filter that adds extra fields to each log record.
        """
        record.thread = self.thread_ident()
        record.threadName = self.thread().name
        record.hostname = self.hostname
        record.process = self.pid
        record.processName = self.process_name
        record.processCommand = self.process_command
        return True

class Manager(multiprocessing.managers.SyncManager):
    pass

class BufferedQueueHandler(logging.handlers.QueueHandler):
    """Buffered queue handler that batches 
    records to improve throughput over remote queues.
    """
    def __init__(self, queue, flush_interval=1, flush_level=logging.CRITICAL):
        """
        Initialise an instance, using the passed queue.
        """
        self.buffer = []
        self.flush_level = flush_level
        self.flush_interval = flush_interval
        self.flush_time = time.time()
        super(BufferedQueueHandler, self).__init__(queue=queue)

    def flush(self):
        """
        Flush records buffer.
        """
        self.acquire()
        try:
            self.flush_time = time.time()
            if self.buffer:
                self.queue.put_nowait(self.buffer)
                self.buffer = []
        finally:
            self.release()
            
    def close(self):
        """
        Close the handler.

        This version just flushes and chains to the parent class' close().
        """
        try:
            self.flush()
        finally:
            return super(BufferedQueueHandler, self).close()

    def enqueue(self, record):
        """
        Enqueue a record.

        The base implementation uses put_nowait. You may want to override
        this method if you want to use blocking, timeouts or custom queue
        implementations.
        """
        self.buffer.append(record)
        if ((time.time() - self.flush_time >= self.flush_interval) or
            (record.levelno >= self.flush_level)):
            self.flush()

class BufferedQueueListener(logging.handlers.QueueListener):
    """Buffered queue listener that can be paired
    with BufferedQueueHandler to process batched records.
    """
    def _monitor(self):
        """
        Monitor the queue for records, and ask the handler
        to deal with them.

        This method runs on a separate, internal thread.
        The thread will terminate if it sees a sentinel object in the queue.
        """
        q = self.queue
        has_task_done = hasattr(q, 'task_done')
        while True:
            try:
                records = self.dequeue(True)
                if records is self._sentinel:
                    if has_task_done:
                        q.task_done()
                    break
                for record in records:
                    self.handle(record)
                if has_task_done:
                    q.task_done()
            except EmptyQueue:
                break

def configure_tracing(main=True, tracer=None):
    """Configure tracing logger.
    """   
    if tracer is None:
        tracer = getLogger("testflows")

    if not settings.trace:
        tracer.setLevel(logging.CRITICAL + 1)
        return

    if main:
        queue = Queue()  
        Manager.register("trace_queue", callable=lambda:queue)
    else:
        Manager.register("trace_queue")

    manager = Manager(address=('', 3360), authkey=b'abc')
    
    if main:
        manager.start()
    else:
        manager.connect()

    queue = manager.trace_queue()

    queue_handler = BufferedQueueHandler(queue)
    queue_handler.addFilter(RecordFilter())

    tracer.addHandler(queue_handler)

    if main:
        file_handler = logging.FileHandler("trace.log", mode="w", encoding="utf-8")
        file_handler.setFormatter(JSONFormatter(indent=None))
        queue_listener_handler = BufferedQueueListener(queue, file_handler) 
        queue_listener_handler.start()

        def _atexit():
            queue_listener_handler.stop()
            queue_handler.close()
            manager.shutdown()
        
        atexit.register(_atexit)

    tracer.setLevel(settings.trace)

    return tracer