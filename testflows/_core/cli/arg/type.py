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
import io
import sys
import argparse

from argparse import ArgumentTypeError
from collections import namedtuple
from testflows._core.exceptions import exception

from testflows._core.compress import CompressedFile

KeyValue = namedtuple("KeyValue", "key value")

class FileType(object):
    def __init__(self, mode='r', bufsize=-1, encoding=None, errors=None):
        self._mode = mode
        self._encoding = encoding
        self._errors = errors

    def __call__(self, string):
        # the special argument "-" means sys.std{in,out}
        if string == '-':
            if 'r' in self._mode:
                try:
                    return io.TextIOWrapper(CompressedFile(sys.stdin.buffer, self._mode), self._encoding, self._errors)
                except Exception as e:
                    print(exception())
                    raise
            elif 'w' in self._mode:
                return sys.stdout
            else:
                msg = argparse._('argument "-" with mode %r') % self._mode
                raise ValueError(msg)

        # all other arguments are used as file names
        try:
            return io.TextIOWrapper(CompressedFile(string, self._mode), self._encoding, self._errors)
        except OSError as e:
            message = argparse._("can't open '%s': %s")
            raise ArgumentTypeError(message % (string, e))

    def __repr__(self):
        args = self._mode
        kwargs = [('encoding', self._encoding), ('errors', self._errors)]
        args_str = ', '.join([repr(arg) for arg in args if arg != -1] +
                             ['%s=%r' % (kw, arg) for kw, arg in kwargs
                              if arg is not None])
        return '%s(%s)' % (type(self).__name__, args_str)


def file(*args, **kwargs):
    """File type."""
    return FileType(*args, **kwargs)

def key_value(s, sep='='):
    """Parse a key, value pair using a seperator (default: '=').
    """
    if sep not in s:
        raise ArgumentTypeError(f"invalid format of key{sep}value")
    key, value= s.split(sep, 1)
    return KeyValue(key.strip(), value.strip())
