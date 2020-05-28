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
import inspect

import testflows._core.objects as objects
from collections import namedtuple as namedtuple

from testflows._core.message import MessageMap, namedtuple_with_defaults
from testflows._core.exceptions import TestFlowsError

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
    pass

class ProjectMessage(Message):
    pass

class EnvironmentMessage(Message):
    pass

class DeviceMessage(Message):
    pass

class SoftwareMessage(Message):
    pass

class HardwareMessage(Message):
    pass

class Prefix(object):
    __slots__ = ()
    fields = "p_keyword p_hash p_ptype, p_num p_stream p_time, p_rtime, p_type p_subtype p_id p_flags p_cflags "
    keyword, hash, ptype, num, stream, time, rtime, type, subtype, id, flags, cflags = list(range(0, 12))

class RawFormat():
    prefix = Prefix

class RawResult(RawFormat, ResultMessage, namedtuple_with_defaults(
        "RawResultMessage",
        RawFormat.prefix.fields + " ".join(objects.Result._fields))):
    pass

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
        RawFormat.prefix.fields + "name uid description attributes requirements " +
            "args tags users tickets examples node map",
        defaults=(None, [], [], [], [], [], [], None, None, None))):
    pass

class RawTag(namedtuple_with_defaults(
        "RawTag",
        " ".join(objects.Tag._fields),
        defaults=objects.Tag._defaults)):
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
        " ".join(objects.Node._fields),
        defaults=objects.Node._defaults)):
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

class RawStop(RawFormat, namedtuple_with_defaults(
        "RawStopMessage",
        RawFormat.prefix.fields)):
    pass

message_map = MessageMap(
     RawNone, # NONE
     RawTest, # TEST
     RawResult, # RESULT
     RawException, # EXCEPTION
     RawNote, # NOTE
     RawDebug, # DEBUG
     RawTrace, # TRACE
     RawVersion,  # VERSION
     RawProtocol,  # PROTOCOL
     RawInput,  # INPUT
     RawValue,  # VALUE
     RawMetric,  # METRIC
     RawTicket,  # TICKET,
     RawArgument, # ARGUMENT
     RawTag, # TAG
     RawAttribute, # ATTRIBUTE
     RawRequirement, # REQUIREMENT
     RawNode, # NODE
     RawMap, # MAP
     RawStop # STOP
 )