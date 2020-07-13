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
from hashlib import sha1
from collections import namedtuple

InitArgs = namedtuple("InitArgs", "args kwargs")

def namedtuple_with_defaults(*args, defaults=()):
    nt = namedtuple(*args)
    nt.__new__.__defaults__ = defaults
    [setattr(nt, f"_{field}", idx) for idx, field in enumerate(nt._fields)]
    return nt

def get(a, b):
    """a if not a is None else b.
    """
    return a if a is not None else b

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

    def __iter__(self):
        return iter([getattr(self, field) for field in self._fields])

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

class Table(tuple, TestObject):
    _fields = ("header", "rows", "row_format")
    _defaults = (None, ) * 3
    _row_type_name = "Row"

    def __new__(cls, header=None, rows=None, row_format=None, _row_type=None):
        if rows is None:
            rows = []
        if header is None:
            header = ""

        if _row_type is None:
            row_type = namedtuple(cls._row_type_name, header)
        else:
            row_type = _row_type

        class Row(row_type):
            def __str__(self):
                s = super(Row, self).__str__()
                return s.split("(", 1)[-1].rstrip(")") or s

            @property
            def __dict__(self):
                return self._asdict()

        obj = super(Table, cls).__new__(cls, [Row(*row) for row in rows])
        obj.initargs=InitArgs(
            args=[header, rows, row_format],
            kwargs={})
        obj.header = header
        obj.rows = obj
        obj.row_type = row_type
        if row_format:
            row_format % tuple(obj.header.split(" "))
        else:
            row_format = Table.default_row_format(row_type._fields, obj[0] if obj else None)
        obj.row_format = row_format
        return obj

    @staticmethod
    def default_row_format(fields, row):
        # if no row_formatter is given then use the header as an example
        # or first row, whichever is longer
        sample_row = fields
        if row and len(str(fields)) < len(str(tuple(row))):
            sample_row = row
        row_format = " | ".join([f"%-{max(len(str(c)), 3)}s" for c in sample_row])
        return row_format

    @staticmethod
    def __str_header__(fields, row_format):
        s = [row_format % fields]
        s.append(row_format % tuple(["-" * len(field) for field in fields]))
        return "\n".join(s)

    @staticmethod
    def __str_row__(row, row_format):
        return row_format % row

    def __str__(self):
        """Return markdown-styled table representation.
        """
        s = [Table.__str_header__(self.row_type._fields, self.row_format)]
        s += [Table.__str_row__(row, self.row_format) for row in self]
        return "\n".join(s)

    @classmethod
    def from_table(cls, table):
        """Creates table from a table.
        """
        return cls(header=" ".join(table.row_type._fields), rows=table, row_format=table.row_format)
