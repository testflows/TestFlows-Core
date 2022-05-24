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
import os
import io
import sys
import csv
import argparse

from argparse import ArgumentTypeError
from collections import namedtuple
from testflows._core.exceptions import exception
from testflows._core.compress import CompressedFile
from testflows._core.objects import Repeat, Retry
from testflows._core.tracing import logging

import testflows._core.contrib.rsa as rsa

KeyValue = namedtuple("KeyValue", "key value")
NoneValue = "__none__"

class FileType(object):
    def __init__(self, mode='r', bufsize=-1, encoding=None, errors=None, safe=False):
        self._mode = mode
        self._bufsize = bufsize
        self._encoding = encoding
        self._errors = errors
        self._safe = safe

    def __call__(self, string):
        # the special argument "-" means sys.std{in,out}
        if string == '-':
            if 'r' in self._mode:
                if 'b' in self._mode:
                    return sys.stdin.buffer
                return sys.stdin
            elif 'w' in self._mode:
                if 'b' in self._mode:
                    return sys.stdout.buffer
                return sys.stdout
            else:
                msg = argparse._('argument "-" with mode %r') % self._mode
                raise ValueError(msg)

        # all other arguments are used as file names
        try:
            if self._safe and os.path.exists(string):
                raise FileExistsError(f"File '{string}' already exists, please delete it first.")

            return open(string, self._mode, self._bufsize, self._encoding,
                        self._errors)
        except OSError as e:
            message = argparse._("can't open '%s': %s")
            raise ArgumentTypeError(message % (string, e))

    def __repr__(self):
        args = self._mode, self._bufsize
        kwargs = [('encoding', self._encoding), ('errors', self._errors)]
        args_str = ', '.join([repr(arg) for arg in args if arg != -1] +
                             ['%s=%r' % (kw, arg) for kw, arg in kwargs
                              if arg is not None])
        return '%s(%s)' % (type(self).__name__, args_str)

class LogFileType(object):
    def __init__(self, mode='r', bufsize=-1, encoding=None, errors=None):
        self._mode = mode
        self._encoding = encoding
        self._errors = errors

    def __call__(self, string):
        # the special argument "-" means sys.std{in,out}
        if string == '-':
            if 'r' in self._mode:
                fp = CompressedFile(sys.stdin.buffer, self._mode)
                if self._encoding:
                    return io.TextIOWrapper(fp, self._encoding, self._errors)
                return fp
            elif 'w' in self._mode:
                fp = CompressedFile(sys.stdout.buffer, self._mode)
                if self._encoding:
                    return io.TextIOWrapper(fp, self._encoding, self._errors)
                return fp
            else:
                msg = argparse._('argument "-" with mode %r') % self._mode
                raise ValueError(msg)

        # all other arguments are used as file names
        try:
            fp = CompressedFile(string, self._mode)
            if self._encoding:
                return io.TextIOWrapper(fp, self._encoding, self._errors)
            return fp
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

def path(p, special=""):
    if p in special or []:
        return p
    if not os.path.exists(os.path.abspath(p)):
        raise ArgumentTypeError(f"path does not exist: '{os.path.abspath(p)}'")
    return p

def file(*args, **kwargs):
    """File type."""
    return FileType(*args, **kwargs)

def logfile(*args, **kwargs):
    """Log file type."""
    return LogFileType(*args, **kwargs)

def rsa_private_key_pem_file(p):
    """RSA private key PEM file type.
    """
    with open(p, mode="rb") as pem_file:
        return rsa.PrivateKey.load_pkcs1(pem_file.read())

def key_value(s, sep='='):
    """Parse a key, value pair using a seperator (default: '=').
    """
    if sep not in s:
        raise ArgumentTypeError(f"invalid format of key{sep}value")
    key, value= s.split(sep, 1)
    return KeyValue(key.strip(), value.strip())

def count(value):
    try:
        value = int(value)
        assert value >= 0
    except:
        raise ArgumentTypeError(f"{value} is not a positive number")
    return value

def repeat(value):
    try:
        fields = list(csv.reader([value], "unix"))[-1]
        until = "fail"
        if len(fields) > 2:
            pattern, count, until = fields
        else:
            pattern, count = fields
        option = Repeat(count=count, pattern=pattern, until=until)
    except Exception as e:
        raise ArgumentTypeError(f"'{value}' is invalid")
    return option

def retry(value):
    try:
        fields = list(csv.reader([value], "unix"))[-1]
        jitter = None # can't be specified
        if len(fields) < 2:
            raise ValueError("needs at least 2 values")
        pattern, count, timeout, delay, backoff = [*fields, *["", None, None, 0, 1][len(fields):]]
        if not pattern:
            pattern = ""
        if not count:
            count = None
        if not timeout:
            timeout = None
        if not delay:
            delay = 0
        if not backoff:
            backoff = 1
        option = Retry(count=count, timeout=timeout, delay=delay, backoff=backoff, jitter=jitter, pattern=pattern)
    except Exception as e:
        raise ArgumentTypeError(f"'{value}' is invalid")
    return option

def tags_filter(value):
    try:
        type, cvstags = value.split(":", 1)
        assert type in ["test", "suite", "module", "feature", "scenario", "any"]
        tags = list(csv.reader([cvstags], "unix"))[-1]
        if type == "scenario":
            type = "test"
        elif type == "feature":
            type = "suite"
        option = (type, tuple(tags))
    except Exception as e:
        raise ArgumentTypeError(f"'{value}' is invalid")
    return option

def onoff(value):
    if value.lower() in ["yes", "1", "on"]:
        return True
    elif value.lower() in ["no", "0", "off"]:
        return False
    elif value == NoneValue:
        return NoneValue
    raise ArgumentTypeError(f"'{value}' is invalid")

onoff.metavar = str(set(["yes", "1", "on", "no", "0", "off"])).replace(" ","").replace("'","")

def trace_level(value):
    if value.lower() in ["debug", "info", "warning", "error", "critical"]:
        return getattr(logging, value.upper())
    else:
        raise ArgumentTypeError(f"'{value}' is invalid")

trace_level.choices = ["debug", "info", "warning", "error", "critical"]
trace_level.metavar = str(set(trace_level.choices)).replace(" ","").replace("'","")