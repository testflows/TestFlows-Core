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
import inspect

import testflows._core.objects as objects
from collections import namedtuple as namedtuple

from testflows._core.message import MessageMap
from testflows._core.exceptions import TestFlowsError

def namedtuple_with_defaults(*args, defaults=()):
    nt = namedtuple(*args)
    nt.__new__.__defaults__ = defaults
    return nt

class Message(object):
    __slots__ = ()

class InvalidMessageError(TestFlowsError):
    pass

class ProtocolMessage(Message):
    pass

class VersionMessage(Message):
    pass

class MetricMessage(Message):
    pass

class TicketMessage(Message):
    pass

class InputMessage(Message):
    pass

class NoteMessage(Message):
    pass

class DebugMessage(Message):
    pass

class TraceMessage(Message):
    pass

class NoneMessage(Message):
    pass

class ExceptionMessage(Message):
    pass

class ValueMessage(Message):
    pass

class TestMessage(Message):
    pass

class ResultMessage(Message):
    def __new__(cls, *args):
        args = list(args)
        l = len(args)
        if l > 13 and args[13]: # metrics
            args[13] = [RawResultMetric(*m) for m in args[13]]
        if l > 14 and args[14]: # tickets
            args[14] = [RawResultTicket(*t) for t in args[14]]
        if l > 15 and args[15]: # values
            args[15] = [RawResultValue(*v) for v in args[15]]
        return super(ResultMessage, cls).__new__(cls, *args)

class OKMessage(ResultMessage):
    pass

class FailMessage(ResultMessage):
    pass

class SkipMessage(ResultMessage):
    pass

class ErrorMessage(ResultMessage):
    pass

class NullMessage(ResultMessage):
    pass

class XOKMessage(ResultMessage):
    pass

class XFailMessage(ResultMessage):
    pass

class XErrorMessage(ResultMessage):
    pass

class XNullMessage(ResultMessage):
    pass

class Prefix(object):
    __slots__ = ()
    fields = "p_keyword p_hash p_num p_type p_subtype p_id p_flags p_cflags p_stream p_time "
    keyword, hash, num, type, subtype, id, flags, cflags, stream, time = list(range(0, 10))

class RawFormat():
    prefix = Prefix

class RawNone(RawFormat, NoneMessage, namedtuple_with_defaults(
        "RawNoneMessage",
        RawFormat.prefix.fields + "message")):
    pass

class RawException(RawFormat, ExceptionMessage, namedtuple_with_defaults(
        "RawExceptionMessage",
        RawFormat.prefix.fields + "exception")):
    pass

class RawTest(RawFormat, TestMessage, namedtuple_with_defaults(
        "RawTestMessage",
        RawFormat.prefix.fields + "name started flags uid description attributes requirements " +
            "args tags users tickets examples node map",
        defaults=(None, None, None, [], [], [], [], [], [], None, None, None))):

    def __new__(cls, *args):
        args = list(args)
        l = len(args)
        if l > 14 and args[14]: # description
            args[14] = RawDescription(args[14])
        if l > 15 and args[15]: # attributes
            args[15] = [RawAttribute(*attr) for attr in args[15]]
        if l > 16 and args[16]: # requirements
            args[16] = [RawRequirement(*req) for req in args[16]]
        if l > 17 and args[17]: # args
            args[17] = [RawArgument(*arg) for arg in args[17]]
        if l > 18 and args[18]: # tags
            args[18] = [RawTag(*tag) for tag in args[18]]
        if l > 19 and args[19]: # users
            args[19] = [RawUser(*user) for user in args[19]]
        if l > 20 and args[20]:  # tickets
            args[20] = [RawTicket(*ticket) for ticket in args[20]]
        if l > 21 and args[21]:  # examples
            args[21] = RawExamples(*args[21])
        if l > 22 and args[22]:  # node
            args[22] = RawNode(*args[22])
        if l > 23 and args[23]:  # maps
            args[23] = RawMap(*args[23])
        return super(RawTest, cls).__new__(cls, *args)

class RawDescription(namedtuple_with_defaults(
        "RawDescription",
        "description")):
    pass

class RawTag(namedtuple_with_defaults(
        "RawTag",
        " ".join(objects.Tag._fields),
        defaults=objects.Tag._defaults)):
    pass

class RawUser(namedtuple_with_defaults(
        "RawUser",
        " ".join(objects.User._fields),
        defaults=objects.User._defaults)):
    pass

class RawTicket(namedtuple_with_defaults(
        "RawTicket",
        " ".join(objects.Ticket._fields),
        defaults=objects.Ticket._defaults)):
    pass

class RawExamples(namedtuple_with_defaults(
        "RawExamples",
        " ".join(objects.ExamplesTable._fields),
        defaults=objects.ExamplesTable._defaults)):
    pass

class RawNode(namedtuple_with_defaults(
        "RawNode",
        " ".join(objects.Node._fields),
        defaults=objects.Node._defaults)):
    pass

class RawMap(namedtuple_with_defaults(
        "RawMap",
        " ".join(objects.Map._fields),
        defaults=objects.Map._defaults)):
    pass

class RawArgument(namedtuple_with_defaults(
        "RawArgument",
        " ".join(objects.Argument._fields),
        defaults=objects.Argument._defaults)):
    pass

class RawAttribute(namedtuple_with_defaults(
        "RawAttribute",
        " ".join(objects.Attribute._fields),
        defaults=objects.Attribute._defaults)):
    pass

class RawRequirement(namedtuple_with_defaults(
        "RawRequirement",
        " ".join(objects.Requirement._fields),
        defaults=objects.Requirement._defaults)):
    pass

class RawResultOK(RawFormat, OKMessage, namedtuple_with_defaults(
        "RawResultOKMessage",
        RawFormat.prefix.fields + " ".join(objects.OK._fields),
        defaults=(None, None, [], [], []))):
    name = "OK"

class RawResultFail(RawFormat, FailMessage, namedtuple_with_defaults(
        "RawResultFailMessage",
        RawFormat.prefix.fields + " ".join(objects.Fail._fields),
        defaults=(None, None, [], [], []))):
    name = "Fail"

class RawResultSkip(RawFormat, SkipMessage, namedtuple_with_defaults(
        "RawResultSkipMessage",
        RawFormat.prefix.fields + " ".join(objects.Skip._fields),
        defaults=(None, None, [], [], []))):
    name = "Skip"

class RawResultError(RawFormat, ErrorMessage, namedtuple_with_defaults(
        "RawResultErrorMessage",
        RawFormat.prefix.fields + " ".join(objects.Error._fields),
        defaults=(None, None, [], [], []))):
    name = "Error"

class RawResultNull(RawFormat, NullMessage, namedtuple_with_defaults(
        "RawResultNullMessage",
        RawFormat.prefix.fields + " ".join(objects.Null._fields),
        defaults=(None, None, [], [], []))):
    name = "Null"

class RawResultXOK(RawFormat, XOKMessage, namedtuple_with_defaults(
        "RawResultXOKMessage",
        RawFormat.prefix.fields + " ".join(objects.XOK._fields),
        defaults=(None, None, [], [], []))):
    name = "XOK"

class RawResultXFail(RawFormat, XFailMessage, namedtuple_with_defaults(
        "RawResultXFailMessage",
        RawFormat.prefix.fields + " ".join(objects.XFail._fields),
        defaults=(None, None, [], [], []))):
    name = "XFail"

class RawResultXError(RawFormat, XErrorMessage, namedtuple_with_defaults(
        "RawResultXErrorMessage",
        RawFormat.prefix.fields + " ".join(objects.XError._fields),
        defaults=(None, None, [], [], []))):
    name = "XError"

class RawResultXNull(RawFormat, XNullMessage, namedtuple_with_defaults(
        "RawResultXNullMessage",
        RawFormat.prefix.fields + " ".join(objects.XNull._fields),
        defaults=(None, None, [], [], []))):
    name = "XNull"

FailResults = [RawResultFail, RawResultError, RawResultNull]
XoutResults = [RawResultXFail, RawResultXError, RawResultXOK, RawResultXNull]

class RawNote(RawFormat, NoteMessage, namedtuple_with_defaults(
        "RawNoteMessage",
        RawFormat.prefix.fields + "message")):
    pass

class RawTrace(RawFormat, TraceMessage, namedtuple_with_defaults(
        "RawTraceMessage",
        RawFormat.prefix.fields + "message")):
    pass

class RawDebug(RawFormat, DebugMessage, namedtuple_with_defaults(
        "RawDebugMessage",
        RawFormat.prefix.fields + "message")):
    pass

class RawInput(RawFormat, InputMessage, namedtuple_with_defaults(
        "RawInputMessage",
        RawFormat.prefix.fields + "message")):
    pass

class RawProtocol(RawFormat, ProtocolMessage, namedtuple_with_defaults(
        "RawProtocolMessage",
        RawFormat.prefix.fields + "version")):
    pass

class RawVersion(RawFormat, VersionMessage, namedtuple_with_defaults(
        "RawVersionMessage",
        RawFormat.prefix.fields + "version")):
    pass

class RawValue(RawFormat, ValueMessage, namedtuple_with_defaults(
        "RawValueMessage",
        RawFormat.prefix.fields + " ".join(objects.Value._fields),
        defaults=objects.Value._defaults)):
    pass

class RawMetric(RawFormat, MetricMessage, namedtuple_with_defaults(
        "RawMetricMessage",
        RawFormat.prefix.fields + " ".join(objects.Metric._fields),
        defaults=objects.Metric._defaults)):
    pass

class RawTicket(RawFormat, TicketMessage, namedtuple_with_defaults(
        "RawTicketMessage",
        RawFormat.prefix.fields + " ".join(objects.Ticket._fields),
        defaults=objects.Ticket._defaults)):
    pass

class RawResultValue(RawFormat, ValueMessage, namedtuple_with_defaults(
        "RawResultValue",
        " ".join(objects.Value._fields),
        defaults=objects.Value._defaults)):
    pass

class RawResultMetric(RawFormat, MetricMessage, namedtuple_with_defaults(
        "RawResultMetric",
        " ".join(objects.Metric._fields),
        defaults=objects.Metric._defaults)):
    pass

class RawResultTicket(RawFormat, TicketMessage, namedtuple_with_defaults(
        "RawResultTicket",
        " ".join(objects.Ticket._fields),
        defaults=objects.Ticket._defaults)):
    pass

message_map = MessageMap(
    RawNone, # NONE
    RawTest, # TEST
    RawResultNull, # NULL
    RawResultOK, # OK
    RawResultFail, # FAIL
    RawResultSkip, # SKIP
    RawResultError, # ERROR
    RawException, # EXCEPTION
    RawValue, # VALUE
    RawNote, # NOTE
    RawDebug, # DEBUG
    RawTrace, # TRACE
    RawResultXOK, #XOK
    RawResultXFail, # XFAIL
    RawResultXError, # XERROR
    RawResultXNull, # XNULL
    RawProtocol, # PROTOCOL
    RawInput, # INPUT
    RawVersion, # VERSION
    RawMetric, # METRIC
    RawTicket, # TICKET
)