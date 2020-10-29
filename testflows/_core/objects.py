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
import base64
import hashlib

from collections import namedtuple

from .utils.enum import IntEnum
from .exceptions import SpecificationError, RequirementError, ResultException
from .baseobject import TestObject, Table
from .baseobject import get, hash
from .baseobject import namedtuple_with_defaults
from .filters import The

import testflows._core.contrib.rsa as rsa

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

XoutResults = (XOK, XFail, XError, XNull)
FailResults = (Fail, Error, Null)
PassResults = (OK,) + XoutResults

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
        name = test.__name__
        module = ".".join([test.__module__, test.__name__])
        uid = hash(module, short=True)
        return cls.NodeAttributes(name, module, uid)

class Tag(TestObject):
    _fields = ("value",)
    _defaults = ()

    def __init__(self, value):
        self.value = value
        return super(Tag, self).__init__()

    def __str__(self):
        return str(self.value)

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

class Specification(TestObject):
    _fields = ("name", "content", "description", "link", "author", "version",
        "date", "status", "approved_by", "approved_date", "approved_version",
        "type", "group", "uid", "parent", "children")
    _defaults = (None,) * 10
    uid = None
    link = None
    type = None
    group = None

    def __init__(self, name, content, description=None, link=None, author=None, version=None,
        date=None, status=None, approved_by=None, approved_date=None, approved_version=None,
        type=None, group=None, uid=None, parent=None, children=None):
        self.name = name
        self.content = content
        self.description = description
        self.author = author
        self.version = version
        self.date = date
        self.status = status
        self.approved_by = approved_by
        self.approved_date = approved_date
        self.approved_version = approved_version
        self.link = get(link, self.link)
        self.type = get(type, self.type)
        self.group = get(group, self.group)
        self.uid = get(uid, self.uid)
        self.parent = parent
        self.children = children

    def __call__(self, *version):
        if not self.version in version:
            raise SpecificationError("specification version %s is not in %s" % (self.version, list(version)))
        return self

class ExamplesRow(TestObject):
    _fields = ("row", "columns", "values", "row_format")
    _defaults = (None,)
    def __init__(self, row, columns, values, row_format=None):
        self.row = row
        self.columns = columns
        self.values = [str(value) for value in values]
        self.row_format = row_format

class Secret(TestObject):
    """RSA encrypted secret.
    """
    _fields = ("name", "code", "pubkey_id", "type", "group", "uid")
    _defaults = (None,) * 6
    uid = None
    name = None
    type = None
    group = None
    encoding = "utf-8"

    def __init__(self, name=None, code=None, pubkey_id=None, type=None, group=None, uid=None):
        self.name = get(name, None)
        self.type = get(type, self.type)
        self.group = get(group, self.group)
        self.uid = get(uid, self.uid)
        self.pubkey_id = get(pubkey_id, None)
        if self.pubkey_id is not None:
            self.pubkey_id = base64.b64decode(pubkey_id.encode(self.encoding))
        self.code = get(code, None)
        self._value = None

        self.__call__(code=code)

    def clear(self):
        self._value = None
        return self

    def __call__(self, value=None, code=None, private_key=None, public_key=None):
        if value is not None:
            self._value = str(value)
            self.code = None

        if code is not None:
            self.code = base64.b64decode(code.encode(self.encoding))
            self._value = None

        if public_key is not None:
            self.pubkey_id = hashlib.sha1(public_key.save_pkcs1()).digest()
            self.code = None

            if self._value is None:
                raise ValueError("no value")
            self.code = rsa.encrypt(self._value.encode(self.encoding), public_key)

        if private_key is not None:
            if self.pubkey_id is not None:
                pk_id = hashlib.sha1(private_key.pubkey.save_pkcs1()).digest()
                if self.pubkey_id != pk_id:
                    raise ValueError("wrong private key")

            if self.code is None:
                raise ValueError("no code")
            self._value = rsa.decrypt(self.code, private_key).decode(self.encoding)

        return self

    @property
    def value(self):
        """Return plaintext value of the secret.
        """
        if self._value is None:
            raise ValueError("no value")
        return self._value

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        """Custom object representation.
        """
        kwargs = []
        for field in self._fields:
            value = getattr(self, field)
            if value is None:
                continue
            if field in ("code", "pubkey_id"):
                kwargs.append(f"{field}='{base64.b64encode(value).decode('utf-8')}'")
            else:
                kwargs.append(f"{field}={repr(value)}")

        return f"Secret({','.join(kwargs)})"

class ExamplesTable(Table):
    _row_type_name = "Example"

    def __new__(cls, header=None, rows=None, row_format=None, args=None):
        if rows is None:
            rows = []
        if header is None:
            header = ""
        if args is None:
            args = {}
        else:
            args = dict(args)

        row_type = namedtuple(cls._row_type_name, header)

        class ExampleRow(row_type):
            def __new__(cls, *args):
                _args = {}
                args = list(args)
                len_header = len(header.split(" "))
                if len(args) > len_header:
                    _args = {k:v for arg in args[len_header:] for k, v in dict(arg).items()}

                    if "type" in args:
                        raise TypeError("can't specify 'type' using example arguments")
                    if "args" in args:
                        raise TypeError("can't specify 'args' using example arguments")

                    del args[len_header:]

                obj = super(ExampleRow, cls).__new__(cls, *args)
                obj._args = _args
                return obj

        obj = super(ExamplesTable, cls).__new__(cls, header, rows, row_format, ExampleRow)

        for idx, row in enumerate(obj):
            row._idx = idx
            row._row_format = obj.row_format

        obj.args = args

        return obj

class NamedValue(object):
    name = None

    def __init__(self, value):
        self.value = value

    def keys(self):
        return [self.name]

    def __getitem__(self, key):
        if key == self.name:
            return self.value
        raise KeyError(key)

    def __call__(self, func):
        setattr(func, self.name, self.value)
        return func

class NamedString(NamedValue):
    def __str__(self):
        return str(self.value)

class NamedList(list):
    name = None

    def __init__(self, *items):
        super(NamedList, self).__init__(items)

    def keys(self):
        return [self.name]

    def __getitem__(self, key):
        if key == self.name:
            return list(self)
        return super(NamedList, self).__getitem__(key)

    def __call__(self, func):
        setattr(func, self.name, list(self))
        return func

class Setup(NamedValue):
    name = "setup"

class XFails(NamedValue):
    """xfails container.

    xfails = {
        "pattern": [("result", "reason")],
        ...
        }
    """
    name = "xfails"

    def __init__(self, value):
        super(XFails, self).__init__(dict(value))

    def items(self):
        return self.value.items()

    def add(self, pattern, *results):
        """Add an entry to the xfails.

        :param pattern: test name pattern to match
        :param *results: one or more results to cross out
            where each result is a two-tuple of (result, reason)
        """
        self.value[pattern] = results
        return self

class XFlags(NamedValue):
    """xflags container.

    xflags = {
        "filter": (set_flags, clear_flags),
        ...
    }
    """
    name = "xflags"

    def __init__(self, value):
        super(XFlags, self).__init__(dict(value))

    def items(self):
        return self.value.items()

    def add(self, pattern, set_flags=0, clear_flags=0):
        """Add an entry to the xflags.

        :param pattern: test name pattern to match
        :param set_flags: flags to set
        :param clear_flags: flags to clear, default: None
        """
        self.value[pattern] = [Flags(set_flags), Flags(clear_flags)]
        return self

class Repeat(NamedList):
    name = "repeat"

    def __init__(self, *repeat):
        super(Repeat, self).__init__(*[RepeatTest(*r) for r in repeat])

class RepeatTest(namedtuple_with_defaults("repeat", "pattern number until", defaults=("fail",))):
    """repeat container."""

    def __new__(cls, *args):
        args = list(args)
        l = len(args)
        if l > 0:
            if not isinstance(args[0], The):
                args[0] = The(args[0])
        if l > 1:
            args[1] = int(args[1])
            assert args[1] > 0
        if l > 2:
            assert args[2] in ("fail", "pass", "complete")
        return super(RepeatTest, cls).__new__(cls, *args)

class Args(dict):
    def __init__(self, **args):
        super(Args, self).__init__(**args)

    def __call__(self, func):
        for k, v in self.items():
            if not k.startswith("_"):
                setattr(func, k, v)
        return func

class Attributes(NamedList):
    name = "attributes"

    def __init__(self, *attributes):
        super(Attributes, self).__init__(*[Attribute(*a) for a in attributes])

class Requirements(NamedList):
    name = "requirements"

    def __init__(self, *requirements):
        super(Requirements, self).__init__(*[Requirement(*r) for r in requirements])

class Specifications(NamedList):
    name = "specifications"

    def __init__(self, *specifications):
        super(Specifications, self).__init__(*[Specification(*r) for r in specifications])

class Tags(NamedList):
    name = "tags"

    def __init__(self, *tags):
        super(Tags, self).__init__(*tags)

class Uid(NamedString):
    name = "uid"

class ArgumentParser(NamedValue):
    name = "argparser"

    def __init__(self, parser):
        self.value = parser

class Name(NamedString):
    name = "name"

class Description(NamedString):
    name = "description"

class Examples(ExamplesTable):
    def __new__(cls, header, rows, row_format=None, args=None):
        return super(Examples, cls).__new__(cls, header=header,
            rows=rows, row_format=row_format, args=args)

    def __call__(self, func):
        func.examples = self
        return func
