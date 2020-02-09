# Copyright 2019 Vitaliy Zakaznikov
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
from hashlib import sha1
from collections import namedtuple

InitArgs = namedtuple("InitArgs", "args kwargs")

def get(a, b):
    """a if not a is None else b.
    """
    return a if not a is None else b

def hash(*s, short=False):
    """Calculate standard hash.
    
    :param s: strings
    :param short: short version, default: False
    """
    value = sha1(''.join(s).encode("utf-8")).hexdigest()[:32]
    if short:
        return value[-16:]
    return value


class TestObject(object):
    """Base class for all the test objects.
    """
    #: object fields used to represent state of the object
    _fields = ()
    #: defaults for the fields
    _defaults = ()

    def __new__(cls, *args, **kwargs):
        obj = super(TestObject, cls).__new__(cls)
        obj.initargs=InitArgs(
            args=[a for a in args],
            kwargs={k: v for k,v in kwargs.items()})
        return obj

    @property
    def id(self):
        return hash(*[repr(getattr(self, field)) for field in self._fields if field != "id"])

    def __repr__(self):
        """Custom object representation.
        """
        args = ",".join([repr(arg) for arg in self.initargs.args])
        kwargs = ",".join([name + "=" + repr(value) for name, value in self.initargs.kwargs.items()])
        name = self.__class__.__name__
        if args and kwargs:
            args += ","
        return "%s(%s%s)" % (name, args, kwargs)


class TestArg(TestObject):
    """Base class for all test argument object.
    """
    pass

class Table(TestObject, tuple):
    _fields = ("header", "rows", "row_format")
    _defaults = (None, ) * 3
    _row_type_name = "Row"

    def __new__(cls, header=None, rows=None, row_format=None):
        if rows is None:
            rows = []
        if header is None:
            header = ""
        row_type = namedtuple(cls._row_type_name, header)
        obj = tuple.__new__(Table, [row_type(*row) for row in rows])
        obj.initargs=InitArgs(
            args=[header, rows, row_format],
            kwargs={})
        obj.header = header
        obj.row_format = row_format
        obj.rows = obj
        obj.row_type = row_type
        # if no row_formatter is given then use the header as an example
        # or first row, whichever is longer
        if obj.row_format is None:
            sample_row = row_type._fields
            if len(obj) > 0 and len(str(row_type._fields)) < len(str(tuple(obj[0]))):
                sample_row = obj[0]
            obj.row_format = " | ".join([f"%-{max(len(str(c)), 3)}s" for c in sample_row])
        return obj

    def __str__(self):
        """Return markdown-styled table representation.
        """
        s = [self.row_format % self.row_type._fields]
        s.append(self.row_format % tuple(["-" * len(field) for field in self.row_type._fields]))
        s += [self.row_format % row for row in self]
        return "\n".join(s)
