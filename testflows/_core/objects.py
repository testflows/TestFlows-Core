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
from enum import IntEnum
from collections import namedtuple

from .utils.enum import IntEnum
from .exceptions import RequirementError, ResultException
from .baseobject import TestObject, TestArg, Table
from .baseobject import get, hash

class Result(TestObject, ResultException):
    _fields = ("message", "reason", "type", "test")
    _defaults = (None,) * 4
    metrics = []
    tickets = []
    values = []
    type = None

    class Type(IntEnum):
        OK = 1
        Fail = 2
        Error = 3
        Null = 4
        Skip = 5
        XOK = 6
        XFail = 7
        XError = 8
        XNull = 9

        def __repr__(self):
            return f"Result.Type.{self._name_}"

    def __init__(self, message=None, reason=None, type=None, test=None, metrics=None, tickets=None, values=None):
        from .funcs import current
        self.test = test if test is not None else current().name
        self.type = get(type, self.type)
        if self.type is None:
            raise TypeError("result type must be defined")
        self.message = message
        self.reason = reason
        self.metrics = get(metrics, list(self.metrics))
        self.tickets = get(tickets, list(self.tickets))
        self.values = get(values, list(self.values))
        return super(Result, self).__init__()

    def __call__(self, result=None):
        if result is None:
            result = getattr(self.__module__, str(self.type))
        obj = result.__class__(*[getattr(result, field) for field in result._fields])
        obj.metrics = self.metrics
        obj.tickets = self.tickets
        obj.values = self.values
        return obj

    def xout(self, reason=None):
        if type(self) in [Result, XResult]:
            return self().xout(reason=reason)
        return self

    def __str__(self):
        return str(self.type)

    def __bool__(cls):
        return True

    def __eq__(self, o):
        return self.type == o.type

    def __ne__(self, o):
        return not self == o

class XResult(Result):
    pass

class OK(Result):
    type = Result.Type.OK
    def xout(self, reason):
        return XOK(test=self.test, message=self.message, reason=reason)

class XOK(XResult):
    type = Result.Type.XOK
    pass

class Fail(Result):
    type = Result.Type.Fail
    def xout(self, reason):
        return XFail(test=self.test, message=self.message, reason=reason)

    def __bool__(self):
        return False

class XFail(XResult):
    type = Result.Type.XFail

class Skip(Result):
    type = Result.Type.Skip

class Error(Result):
    type = Result.Type.Error

    def xout(self, reason):
        return XError(test=self.test, message=self.message, reason=reason)

    def __bool__(self):
        return False

class XError(XResult):
    type = Result.Type.XError

class Null(Result):
    type = Result.Type.Null

    def xout(self, reason):
        return XNull(test=self.test, message=self.message, reason=reason)

    def __bool__(self):
        return False

class XNull(XResult):
    type = Result.Type.XNull

class Node(TestObject):
    _fields = ("name", "module", "uid", "nexts", "ins", "outs")
    _defaults = (None,) * 3

    NodeAttributes = namedtuple("NodeAttributes", "name module uid")

    def __init__(self, name, module, uid, nexts=None, ins=None, outs=None):
        self.name = name
        self.module = module
        self.uid = uid
        self.nexts = get(nexts, [])
        self.ins = get(ins, [])
        self.outs =get(outs, [])
        return super(Node, self).__init__()

    @classmethod
    def attributes(cls, test):
        name = test.name
        module = ".".join([test.__module__, test.name])
        uid = hash(module, short=True)
        return cls.NodeAttributes(name, module, uid)

def maps(test, nexts=None, ins=None, outs=None, map=[]):
    """Map a test.

    :param test: test
    :param nexts: next steps
    :param ins: input steps
    :param outs: output steps
    """
    if getattr(test.func, "node", None) is not None:
        raise ValueError("test has already been mapped")

    nexts = [Node.attributes(step).uid for step in nexts or []]
    ins = [Node.attributes(step).uid for step in ins or []]
    outs = [Node.attributes(step).uid for step in outs or []]

    test.func.node = Node(*Node.attributes(test), nexts, ins, outs)

    map.append(test.func.node)
    return map

class Tag(TestObject):
    _fields = ("value",)
    _defaults = ()

    def __init__(self, value):
        self.value = value
        return super(Tag, self).__init__()

class Argument(TestObject):
    _fields = ("name", "value", "type", "group", "uid")
    _defaults = (None,) * 4
    uid = None
    type = None
    group = None

    def __init__(self, name, value=None, type=None, group=None, uid=None):
        self.name = name
        self.value = value
        self.type = get(type, self.type)
        self.group = get(group, self.group)
        self.uid = get(uid, self.uid)
        return super(Argument, self).__init__()

class Attribute(TestObject):
    _fields = ("name", "value", "type", "group", "uid")
    _defaults = (None,) * 3
    uid = None
    type = None
    group = None
    
    def __init__(self, name, value, type=None, group=None, uid=None):
        self.name = name
        self.value = value
        self.type = get(type, self.type)
        self.group = get(group, self.group)
        self.uid = get(uid, self.uid)
        return super(Attribute, self).__init__()

class Requirement(TestObject):
    _fields = ("name", "version", "description",
            "link", "priority", "type", "group", "uid")
    _defaults = (None,) * 6
    uid = None
    link = None
    priority = None
    type = None
    group = None
    
    def __init__(self, name, version, description=None, link=None,
            priority=None, type=None, group=None, uid=None):
        self.name = name
        self.version = version
        self.description = get(description, self.__doc__)
        self.link = get(link, self.link)
        self.priority = get(priority, self.priority)
        self.type = get(type, self.type)
        self.group = get(group, self.group)
        self.uid = get(uid, self.uid)
        return super(Requirement, self).__init__()  

    def __call__(self, *version):
        if not self.version in version:
            raise RequirementError("requirement version %s is not in %s" % (self.version, list(version)))
        return self

class Metric(TestObject):
    _fields = ("name", "value", "units", "type", "group", "uid")
    _defaults = (None,) * 3
    uid = None
    type = None
    group = None
    
    def __init__(self, name, value, units, type=None, group=None, uid=None):
        self.name = name
        self.value = value
        self.units = units
        self.type = get(type, self.type)
        self.group = get(group, self.group)
        self.uid = get(uid, self.uid)
        return super(Metric, self).__init__()

class Value(TestObject):
    _fields = ("name", "value", "type", "group", "uid")
    _defaults = (None,) * 3
    uid = None
    type = None
    group = None

    def __init__(self, name, value, type=None, group=None, uid=None):
        self.name = name
        self.value = str(value)
        self.type = get(type, self.type)
        self.group = get(group, self.group)
        self.uid = get(uid, self.uid)
        return super(Value, self).__init__()

class Ticket(TestObject):
    _fields = ("name", "link", "type", "group", "uid")
    _defaults = (None,) * 4
    uid = None
    link = None
    type = None
    group = None
    
    def __init__(self, name, link=None, type=None, group=None, uid=None):
        self.name = name
        self.link = get(link, self.link)
        self.type = get(type, self.type)
        self.group = get(group, self.group)
        self.uid = get(uid, self.uid)
        return super(Ticket, self).__init__()

class Example(TestObject):
    _fields = ("row", "columns", "values", "row_format")
    _defaults = (None,)
    def __init__(self, row, columns, values, row_format=None):
        self.row = row
        self.columns = columns
        self.values = [str(value) for value in values]
        self.row_format = row_format

class ExamplesTable(Table):
    _row_type_name = "Example"

    @classmethod
    def from_table(cls, table):
        """Create examples table from a table.
        """
        return cls(header=" ".join(table.row_type._fields), rows=table, row_format=table.row_format)
