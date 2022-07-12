# Copyright 2019 Katteli Inc.
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
import time
import threading

from multiprocessing.dummy import Pool

import testflows.settings as settings
import testflows._core.tracing as tracing

from .compress import compress
from .constants import id_sep, end_of_message
from .exceptions import exception as get_exception
from .message import Message, MessageObjectType, dumps
from .objects import Tag, ExamplesRow
from . import __version__
from .parallel.service import BaseServiceObject

tracer = tracing.getLogger(__name__)

def object_fields(obj, prefix):
    return {f"{prefix}{'_' if prefix else ''}{field}":getattr(obj, field) for field in obj._fields}

def str_or_repr(v):
    try:
        return str(v)
    except:
        return repr(v)

class TestOutput(object):
    """Test output protocol.

    :param io: message IO
    """
    protocol_version = "TFSPv2.1"

    def __init__(self, test, io):
        self.io = io
        self.test = test
        self.msg_hash = ""
        self.msg_count = 0
        self.prefix = {
            "test_type": str(self.test.type),
            "test_subtype": str(self.test.subtype) if self.test.subtype is not None else None,
            "test_id": self.test.id_str,
            "test_name": self.test.name,
            "test_flags": int(self.test.flags),
            "test_cflags": int(self.test.cflags),
            "test_level": len(self.test.id),
            "test_parent_type": str(self.test.parent_type) if self.test.parent_type is not None else None
        }

    def message(self, keyword, message, object_type=0, stream=None):
        """Output message.

        :param keyword: keyword
        :param message: message
        """
        msg_time = time.time()

        msg = {
            "message_keyword": str(keyword),
            "message_hash": self.msg_hash,
            "message_object": object_type,
            "message_num": self.msg_count,
            "message_stream": stream,
            "message_level": (
                len(self.test.id) + 1
                if keyword not in (Message.TEST, Message.RESULT, Message.PROTOCOL, Message.VERSION)
                else len(self.test.id)
            ),
            "message_time": round(msg_time, settings.time_resolution),
            "message_rtime": round(msg_time - self.test.start_time, settings.time_resolution)
        }
        msg.update(self.prefix)

        if settings.secrets_registry:
            if not settings.secrets_registry.is_empty():
                if "message" in message and message["message"]:
                    message["message"] = settings.secrets_registry.filter(message["message"])
                if "result_message" in message and message["result_message"]:
                    message["result_message"] = settings.secrets_registry.filter(message["result_message"])
                if "test_description" in message and message["test_description"]:
                    message["test_description"] = settings.secrets_registry.filter(message["test_description"])
                if "argument_value" in message and message["argument_value"]:
                    message["argument_value"] = settings.secrets_registry.filter(message["argument_value"])

        msg.update(message)
        self.test.tracer.debug("test message", extra={"test_message":msg})

        msg = dumps(msg)

        self.msg_hash = settings.hash_func(msg.encode("utf-8")).hexdigest()[:settings.hash_length]
        self.msg_count += 1

        parts = msg.split(",",2)
        parts[1] = f"\"message_hash\":\"{self.msg_hash}\""
        self.io.write(f"{parts[0]},{parts[1]},{parts[2]}{end_of_message}")

    def stop(self):
        """Output stop message."""
        self.message(Message.STOP, {})

    def protocol(self):
        """Output protocol version message.
        """
        msg = {"protocol_version": self.protocol_version}
        self.message(Message.PROTOCOL, msg)

    def version(self):
        """Output framework version message.
        """
        msg = {"framework_version": __version__}
        self.message(Message.VERSION, msg)

    def prompt(self, message):
        """Output prompt message.

        :param message: message
        """
        msg = {"message": str(message)}
        self.message(Message.PROMPT, msg)

    def input(self, message):
        """Output input message.

        :param message: message
        """
        msg = {"message": str(message)}
        self.message(Message.INPUT, msg)

    def exception(self, exc_type=None, exc_value=None, exc_traceback=None):
        """Output exception message.

        Note: must be called from within finally block
        """
        msg = {"message": get_exception(exc_type, exc_value, exc_traceback)}
        self.message(Message.EXCEPTION, msg)

    def test_message(self):
        """Output test message.
        """
        msg = {
            "test_name": self.test.name,
            "test_uid": str(self.test.uid or "") or None,
            "test_description": str(self.test.description or "") or None,
        }

        self.message(Message.TEST, msg, object_type=MessageObjectType.TEST)

        [self.attribute(attr) for attr in self.test.attributes.values()]
        [self.specification(spec) for spec in self.test.specifications.values()]
        [self.requirement(req) for req in self.test.requirements.values()]
        [self.argument(arg) for arg in self.test.args.values()]
        [self.tag(Tag(tag)) for tag in self.test.tags]
        [self.example(ExamplesRow(row._idx, row._fields, [str(f) for f in row], row._row_format)) for row in self.test.examples]
        if self.test.node:
            self.node(self.test.node)
        if self.test.map:
            self.map(self.test.map)

    def attribute(self, attribute, object_type=MessageObjectType.TEST):
        msg = object_fields(attribute, "attribute")
        value = msg["attribute_value"]
        if value is not None:
            msg["attribute_value"] = str_or_repr(value)
        self.message(Message.ATTRIBUTE, msg, object_type=object_type)

    def requirement(self, requirement, object_type=MessageObjectType.TEST):
        msg = object_fields(requirement, "requirement")
        self.message(Message.REQUIREMENT, msg, object_type=object_type)

    def specification(self, specification, object_type=MessageObjectType.TEST):
        msg = object_fields(specification, "specification")
        _requirements = []
        for req in msg["specification_requirements"] or []:
            _requirements.append(object_fields(req, ""))
        msg["specification_requirements"] = _requirements
        self.message(Message.SPECIFICATION, msg, object_type=object_type)

    def argument(self, argument, object_type=MessageObjectType.TEST):
        msg = object_fields(argument, "argument")
        value = msg["argument_value"]
        if value is not None:
            msg["argument_value"] = str_or_repr(value)
        self.message(Message.ARGUMENT, msg, object_type=object_type)

    def tag(self, tag, object_type=MessageObjectType.TEST):
        msg = object_fields(tag, "tag")
        self.message(Message.TAG, msg, object_type=object_type)

    def example(self, example, object_type=MessageObjectType.TEST):
        msg = object_fields(example, "example")
        self.message(Message.EXAMPLE, msg, object_type=object_type)

    def node(self, node, object_type=MessageObjectType.TEST):
        msg = object_fields(node, "node")
        self.message(Message.NODE, msg, object_type=object_type)

    def map(self, map, object_type=MessageObjectType.TEST):
        for node in map:
            msg = object_fields(node, "node")
            self.message(Message.MAP, msg, object_type=object_type)

    def ticket(self, ticket, object_type=MessageObjectType.TEST):
        msg = object_fields(ticket, "ticket")
        self.message(Message.TICKET, msg, object_type=object_type)

    def metric(self, metric, object_type=MessageObjectType.TEST):
        msg = object_fields(metric, "metric")
        self.message(Message.METRIC, msg, object_type=object_type)

    def value(self, value, object_type=MessageObjectType.TEST):
        msg = object_fields(value, "value")
        self.message(Message.VALUE, msg, object_type=object_type)

    def result(self, result):
        """Output result message.

        :param result: result object
        """
        msg = {
            "result_message": result.message,
            "result_reason": result.reason,
            "result_type": str(result.type),
            "result_test": result.test
        }
        self.message(Message.RESULT, msg, object_type=MessageObjectType.TEST)

    def text(self, message):
        """Output text message.

        :param message: message
        """
        msg = {"message": str(message)}
        self.message(Message.TEXT, msg)

    def note(self, message):
        """Output note message.

        :param message: message
        """
        msg = {"message": str(message)}
        self.message(Message.NOTE, msg)

    def debug(self, message):
        """Output debug message.

        :param message: message
        """
        msg = {"message": str(message)}
        self.message(Message.DEBUG, msg)

    def trace(self, message):
        """Output trace message.

        :param message: message
        """
        msg = {"message": str(message)}
        self.message(Message.TRACE, msg)

class TestInput(object):
    """Test input.
    """
    def __init__(self, test, io):
        self.test = test
        self.io = io


class TestIO(object):
    """Test input and output protocol.
    """
    def __init__(self, test):
        self.io = MessageIO(LogIO())
        self.output = TestOutput(test, self.io)
        self.input = TestInput(test, self.io)

    def message_io(self, name=None):
        """Return named line buffered message io.

        :param name: name of the message stream
        """
        return NamedMessageIO(self, name=name)

    def read(self, topic, timeout=None):
        """Read message.

        :param topic: message topic
        :param timeout: timeout, default: ``None``
        """
        raise NotImplementedError

    def write(self, msg, stream=None):
        """Write line buffered message.

        :param msg: line buffered message
        :param stream: name of the stream
        """
        if not msg:
            return
        self.output.message(Message.NONE, {"message":str(msg).rstrip()}, stream=stream)

    def flush(self):
        self.io.flush()

    def close(self, flush=False, final=False):
        self.io.close(flush=flush, final=final)

class MessageIO(object):
    """Message input and output.

    :param io: io stream to write and read
    """

    def __init__(self, io):
        self.io = io
        self.buffer = ""

    def read(self, topic, timeout=None):
        """Read message.

        :param topic: message topic
        :param timeout: timeout, default: ``None``
        """
        raise NotImplementedError

    def write(self, msg):
        """Write message.

        :param msg: message
        """
        if not msg:
            return
        if msg[-1] == "\n" and not self.buffer:
            self.io.write(msg)
        elif msg.endswith("\n") or "\n" in msg:
            self.buffer += msg
            messages = self.buffer.split("\n")
            # last message is incomplete
            for message in messages[:-1]:
                self.io.write(f"{message}\n")
            self.buffer = messages[-1]
        else:
            self.buffer += msg

    def flush(self):
        """Flush output buffer.
        """
        if self.buffer:
            self.io.write(f"{self.buffer}\n")
        self.buffer = ""

    def close(self, flush=False, final=False):
        self.io.close(flush=flush, final=final)

class NamedMessageIO(MessageIO):
    """Message input and output.

    :param io: io stream to write and read
    :param name: name of the stream, default: None
    """

    def __init__(self, io, name=None):
        self.io = io
        self.buffer = ""
        self.stream = name

    def write(self, msg):
        """Write message.

        :param msg: message
        """
        if not msg:
            return
        if not "\n" in msg:
            self.buffer += msg
        else:
            self.buffer += msg
            messages = self.buffer.split("\n")
            # last message is incomplete
            for message in messages[:-1]:
                self.io.write(f"{message}\n", stream=self.stream)
            self.buffer = messages[-1]

    def flush(self):
        """Flush output buffer.
        """
        if self.buffer:
            self.io.write(f"{self.buffer}\n", stream=self.stream)
        self.buffer = ""


class ProtectedFile:
    """Thread lock wrapped file descriptor.
    """ 
    def __init__(self, fd):
        self.fd = fd
        self.lock = threading.Lock()
    
    def write(self, *args, **kwargs):
        with self.lock:
            return self.fd.write(*args, **kwargs)

    def read(self, *args, **kwargs):
        with self.lock:
            return self.fd.read(*args, **kwargs)

    def flush(self, *args, **kwargs):
        with self.lock:
            return self.fd.flush(*args, **kwargs)

    def close(self, *args, **kwargs):
        with self.lock:
            return self.fd.close(*args, **kwargs)

    def tell(self, *args, **kwargs):
        with self.lock:
            return self.fd.tell(*args, **kwargs)

    def seek(self, *args, **kwargs):
        with self.lock:
            return self.fd.seek(*args, **kwargs)


class LogReader(object):
    """Read messages from the log.
    """
    lock = threading.Lock()
    fd = None

    def __new__(cls, *args, **kwargs):
        fd = kwargs.pop("fd", None)

        with cls.lock:
            if not cls.fd:
                cls.fd = fd or ProtectedFile(open(settings.read_logfile, "rb", buffering=0))

            return object.__new__(LogReader)

    def __init__(self, fd=None):
        self.fd = fd or self.__class__.fd

    def tell(self):
        return self.fd.tell()

    def seek(self, pos):
        return self.fd.seek(pos)

    def read(self, topic, timeout=None):
        raise NotImplementedError

    def close(self, final=False):
        if final:
            self.fd.close()


class LogWriter(object):
    """Singleton log file writer.
    """
    lock = threading.Lock()
    instance = None
    auto_flush_interval = 0.15

    def __new__(cls, *args, **kwargs):
        fd = kwargs.pop("fd", None)

        with cls.lock:
            if not cls.instance:
                self = object.__new__(LogWriter)
                self.fd = fd or ProtectedFile(open(settings.write_logfile, "ab", buffering=0))
                self.lock = threading.Lock()
                self.buffer = []
                self.pool = Pool(1)
                self.cancel = False
                self.pool.apply_async(self.flush, (), dict(sleep=cls.auto_flush_interval, force=True))
                cls.instance = self
            return cls.instance

    def __init__(self, *args, **kwargs):
        pass

    def write(self, msg):
        with self.lock:
            self.buffer.append(msg.encode("utf-8"))
            return len(msg)

    def flush(self, force=False, final=False, sleep=None):
        if not force:
            return

        if sleep:
            time.sleep(sleep)

        if self.cancel:
            return

        with self.lock:
            self.cancel = True
            if self.buffer:
                self.fd.write(compress(b"".join(self.buffer)))
                self.fd.flush()
                del self.buffer[:]

            if not final and threading.main_thread().is_alive():
                self.cancel = False
                self.pool.apply_async(self.flush, (), dict(sleep=self.auto_flush_interval, force=True))

    def close(self, flush=False, final=False):
        if final:
            self.pool.close()
            self.flush(force=True, final=True)
            self.fd.close()
            self.pool.join()
        elif flush:
            self.flush(force=True)


class LogIO(object):
    """Log file reader and writer.

    :param read: file descriptor for read
    :param write: file descriptor for write
    """
    def __init__(self):
        if isinstance(settings.write_logfile, BaseServiceObject):
            self.writer = LogWriter(fd=settings.write_logfile)
        else:
            self.writer = LogWriter()
        
        if isinstance(settings.read_logfile, BaseServiceObject):
            self.reader = LogReader(fd=settings.read_logfile)
        else:
            self.reader = LogReader()

    def write(self, msg):
        return self.writer.write(msg)

    def flush(self):
        return self.writer.flush()

    def tell(self):
        return self.reader.tell()

    def seek(self, pos):
        return self.reader.seek(pos)

    def read(self, topic, timeout=None):
        return self.reader.read(topic, timeout)

    def close(self, flush=False, final=False):
        self.writer.close(flush=flush, final=final)
        self.reader.close(final=final)
