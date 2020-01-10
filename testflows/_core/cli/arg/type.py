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
from argparse import FileType
from argparse import ArgumentTypeError

from collections import namedtuple

KeyValue = namedtuple("KeyValue", "key value")

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
