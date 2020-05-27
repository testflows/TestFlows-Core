# Copyright 2019 Katteli Inc.
# TestFlows Test Framework (http://testflows.com)
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
import re
import sys
import time
import threading

import testflows.settings as settings

from .constants import id_sep, end_of_message
from .exceptions import exception as get_exception
from .message import Message, MessageParentObjectType, MessageParentObjectIds, dumps
from .objects import Tag, Metric, Example
from .funcs import top
from . import __version__

def object_fields(obj, prefix):
    return {f"{prefix}_{field}":getattr(obj, field) for field in obj._fields}

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
            "test_id": id_sep + id_sep.join(str(n) for n in self.test.id),
            "test_flags": int(self.test.flags),
            "test_cflags": int(self.test.cflags)
        }

    def message(self, keyword, message, ptype=0, pids=None, stream=None):
        """Output message.

        :param keyword: keyword
        :param message: message
        """
        msg_time = time.time()

        msg = {
            "message_keyword": str(keyword),
            "message_hash": self.msg_hash,
            "message_ptype": ptype,
            "message_num": self.msg_count,
            "message_stream": stream,
            "message_time": round(msg_time, settings.time_resolution),
            "message_rtime": round(msg_time - self.test.start_time, settings.time_resolution)
        }
        msg.update(self.prefix)
        msg.update(message)

        if pids:
            msg.update(pids._asdict())

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
        ptype = MessageParentObjectType.TEST
        msg = {
            "test_name": self.test.name,
            "test_uid": str(self.test.uid or "") or None,
            "test_description": str(self.test.description or "") or None,
        }

        self.message(Message.TEST, msg, ptype=ptype)

        [self.attribute(attr, ptype=ptype) for attr in self.test.attributes]
        [self.requirement(req, ptype=ptype) for req in self.test.requirements]
        [self.argument(arg, ptype=ptype) for arg in self.test.args.values()]
        [self.tag(Tag(tag), ptype=ptype) for tag in self.test.tags]
        [self.user(user, ptype=ptype) for user in self.test.users]
        [self.example(Example(idx, col, getattr(row, col)), ptype=ptype) for idx, row in enumerate(self.test.examples) for col in row._fields]
        if self.test.node:
            self.node(self.test.node, ptype=ptype)
        if self.test.map:
            self.map(self.test.map, ptype=ptype)

    def attribute(self, attribute, ptype):
        msg = object_fields(attribute, "attribute")
        self.message(Message.ATTRIBUTE, msg, ptype=ptype)

    def requirement(self, requirement, ptype):
        msg = object_fields(requirement, "requirement")
        self.message(Message.REQUIREMENT, msg, ptype=ptype)

    def argument(self, argument, ptype):
        msg = object_fields(argument, "argument")
        value = msg["argument_value"]
        if value is not None:
            msg["argument_value"] = str_or_repr(value)
        self.message(Message.ARGUMENT, msg, ptype=ptype)

    def tag(self, tag, ptype):
        msg = object_fields(tag, "tag")
        self.message(Message.TAG, msg, ptype=ptype)

    def user(self, user, ptype):
        msg = object_fields(user, "user")
        self.message(Message.USER, msg, ptype=ptype)

    def example(self, example, ptype):
        msg = object_fields(example, "example")
        self.message(Message.EXAMPLE, msg, ptype=ptype)

    def node(self, node, ptype):
        msg = object_fields(node, "node")
        self.message(Message.NODE, msg, ptype=ptype)

    def map(self, map, ptype):
        for node in map:
            msg = object_fields(node, "node")
            self.message(Message.MAP, msg, ptype=ptype)

    def ticket(self, ticket, ptype=MessageParentObjectType.TEST | MessageParentObjectType.RESULT):
        msg = object_fields(ticket, "ticket")
        self.message(Message.TICKET, msg, ptype=ptype)

    def metric(self, metric, ptype=MessageParentObjectType.TEST | MessageParentObjectType.RESULT):
        msg = object_fields(metric, "metric")
        self.message(Message.METRIC, msg, ptype=ptype)

    def value(self, value, ptype=MessageParentObjectType.TEST | MessageParentObjectType.RESULT):
        msg = object_fields(value, "value")
        self.message(Message.VALUE, msg, ptype=ptype)

    def result(self, result):
        """Output result message.

        :param result: result object
        """
        ptype = MessageParentObjectType.TEST | MessageParentObjectType.RESULT
        msg = {
            "result_message": result.message,
            "result_reason": result.reason,
            "result_type": str(result.type),
        }
        self.message(Message.RESULT, msg, ptype=ptype)

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
        self.output.message(Message.NONE, dumps({"message":str(msg).rstrip()}), stream=stream)

    def flush(self):
        self.io.flush()

    def close(self):
        self.io.close()

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

    def close(self):
        self.io.close()

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


class LogReader(object):
    """Read messages from the log.
    """
    def __init__(self):
        self.fd = open(settings.read_logfile, "r", buffering=1, encoding="utf-8")

    def tell(self):
        return self.fd.tell()

    def seek(self, pos):
        return self.fd.seek(pos)

    def read(self, topic, timeout=None):
        raise NotImplementedError

    def close(self):
        self.fd.close()


class LogWriter(object):
    """Singleton log file writer.
    """
    lock = threading.Lock()
    instance = None

    def __new__(cls, *args, **kwargs):
        with cls.lock:
            if not cls.instance:
                self = object.__new__(LogWriter)
                self.fd = open(settings.write_logfile, "a", buffering=1, encoding="utf-8")
                self.lock = threading.Lock()
                cls.instance = self
            return cls.instance

    def __init__(self):
        pass

    def write(self, msg):
        with self.lock:
            n = self.fd.write(msg)
            self.fd.flush()
            return n

    def flush(self):
        with self.lock:
            return self.fd.flush()

    def close(self):
        pass

class LogIO(object):
    """Log file reader and writer.

    :param read: file descriptor for read
    :param write: file descriptor for write
    """
    def __init__(self):
        self.writer = LogWriter()
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

    def close(self):
        self.writer.close()
        self.reader.close()

