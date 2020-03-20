# Copyright 2019 Vitaliy Zakaznikov (TestFlows Test Framework http://testflows.com)
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

from .serialize import dumps
from .constants import id_sep, end_of_message
from .exceptions import exception as get_exception
from .message import Message
from .objects import Tag, Node, Map, Metric
from .funcs import top
from . import __version__

def object_fields(obj):
    return [getattr(obj, field) for field in obj._fields]

def rstrip_list(l, value=[None, []]):
    """Remove all the items matching the value
    from the end of the list
    """
    while True:
        if l and l[-1] in value:
            l.pop(-1)
            continue
        break
    return l

class TestOutput(object):
    """Test output protocol.

    :param io: message IO
    """
    rstrip_nulls = re.compile(r'(,null)+$')
    protocol_version = "TFSPv1.4"

    def __init__(self, test, io):
        self.io = io
        self.test = test
        self.msg_hash = ""
        self.msg_count = 0
        self.prefix = dumps([
            int(self.test.type),
            int(self.test.subtype),
            id_sep + id_sep.join(str(n) for n in self.test.id),
            int(self.test.flags),
            int(self.test.cflags)
        ])[1:-1]

    def message(self, keyword, message, rtime=None, stream=None):
        """Output message.

        :param keyword: keyword
        :param message: message
        :param rtime: relative time, default: None
        """
        rtime = rtime
        if rtime is None:
            rtime = round(time.time() - self.test.start_time, settings.time_resolution)
        msg = f"{self.msg_count},{self.prefix},{dumps(stream)},{rtime:.{settings.time_resolution}f},{str(message)}{end_of_message}"
        msg = self.rstrip_nulls.sub("", msg)
        msg_hash = settings.hash_func(f"{self.msg_hash},{keyword},{msg}".encode("utf-8")).hexdigest()[:settings.hash_length]
        self.msg_count += 1
        self.msg_hash = msg_hash
        self.io.write(f"{keyword},\"{msg_hash}\",{msg}")

    def protocol(self):
        """Output protocol version message.
        """
        msg = dumps(str(self.protocol_version))
        self.message(Message.PROTOCOL, msg, rtime=round(self.test.start_time, settings.time_resolution))

    def version(self):
        """Output framework version message.
        """
        msg = dumps(str(__version__))
        self.message(Message.VERSION, msg, rtime=round(self.test.start_time, settings.time_resolution))

    def input(self, message):
        """Output input message.

        :param message: message
        """
        msg = dumps(str(message))
        self.message(Message.INPUT, msg)

    def exception(self):
        """Output exception message.

        Note: must be called from within finally block
        """
        msg = dumps(get_exception())
        self.message(Message.EXCEPTION, msg)

    def test_message(self):
        """Output test message.

        :param test: test object
        """
        def str_or_repr(v):
            try:
                return str(v)
            except:
                return repr(v)

        def map_fields(obj, visited):
            visited.add(obj.node)
            return rstrip_list([
                rstrip_list(object_fields(Node.create(obj.node))),
                rstrip_list([map_fields(
                    Map(n) if n in visited else getattr(n.func, "map", Map(n)), visited)
                        for n in obj.nexts]) if obj.nexts else None,
                rstrip_list([map_fields(
                    Map(n) if n in visited else getattr(n.func, "map", Map(n)), visited)
                        for n in obj.ins]) if obj.ins else None,
                rstrip_list([map_fields(
                    Map(n) if n in visited else getattr(n.func, "map", Map(n)), visited)
                        for n in obj.outs]) if obj.outs else None,
            ])

        msg = dumps(rstrip_list([
            self.test.name,
            round(self.test.start_time, settings.time_resolution),
            str(self.test.flags) or None,
            str(self.test.uid or "") or None,
            str(self.test.description or "") or None,
            [rstrip_list(object_fields(attr)) for attr in self.test.attributes],
            [rstrip_list(object_fields(req)) for req in self.test.requirements],
            [[str_or_repr(a) for a in rstrip_list(object_fields(arg))] for arg in self.test.args.values()],
            [rstrip_list(object_fields(Tag(tag))) for tag in self.test.tags],
            [rstrip_list(object_fields(user)) for user in self.test.users],
            [rstrip_list(object_fields(ticket)) for ticket in self.test.tickets],
            rstrip_list(object_fields(self.test.examples)) if self.test.examples else None,
            rstrip_list(object_fields(self.test.node)) if self.test.node else None,
            map_fields(self.test.map, set()) if (self.test.map and self.test is top()) else None
        ]))[1:-1]
        self.message(Message.TEST, msg, rtime=0)

    def ticket(self, ticket):
        msg = dumps(rstrip_list(object_fields(ticket)))[1:-1]
        self.message(Message.TICKET, msg)

    def metric(self, metric):
        msg = dumps(rstrip_list(object_fields(metric)))[1:-1]
        self.message(Message.METRIC, msg)

    def value(self, value):
        msg = dumps(rstrip_list(object_fields(value)))[1:-1]
        self.message(Message.VALUE, msg)

    def result(self, result):
        """Output result message.

        :param result: result object
        """
        msg = dumps(rstrip_list([
            self.test.name,
            result.message,
            result.reason,
            [rstrip_list(object_fields(m)) for m in result.metrics],
            [rstrip_list(object_fields(t)) for t in result.tickets],
            [rstrip_list(object_fields(v)) for v in result.values],
        ]))[1:-1]
        self.message(getattr(Message, result.__class__.__name__.upper()), msg)

    def note(self, message):
        """Output note message.

        :param message: message
        """
        msg = dumps(str(message))
        self.message(Message.NOTE, msg)

    def debug(self, message):
        """Output debug message.

        :param message: message
        """
        msg = dumps(str(message))
        self.message(Message.DEBUG, msg)

    def trace(self, message):
        """Output trace message.

        :param message: message
        """
        msg = dumps(str(message))
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
        self.output.message(Message.NONE, dumps(str(msg).rstrip()), stream=stream)

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
        if not "\n" in msg:
            self.buffer += msg
        else:
            self.buffer += msg
            messages = self.buffer.split("\n")
            # last message is incomplete
            for message in messages[:-1]:
                self.io.write(f"{message}\n")
            self.buffer = messages[-1]

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
    '''Read messages from the log.
    '''
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
    '''Singleton log file writer.
    '''
    lock = threading.Lock()
    instance = None

    def __new__(cls, *args, **kwargs):
        if not LogWriter.instance:
            LogWriter.instance = object.__new__(LogWriter)
        return LogWriter.instance

    def __init__(self):
        self.fd = open(settings.write_logfile, "a", buffering=1, encoding="utf-8")
        self.lock = threading.Lock()

    def write(self, msg):
        '''Write line buffered messages.

        :param msg: line buffered messages
        '''
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
    '''Log file reader and writer.

    :param read: file descriptor for read
    :param write: file descriptor for write
    '''
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

