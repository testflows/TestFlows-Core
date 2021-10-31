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
# to the end flag
from .name import absname, match
from .baseobject import TestObject
from .testtype import TestType

class The(TestObject):
    """The `only`, `skip`, `start` and `end` test filer object.
    """
    _fields = ("pattern",)

    def __init__(self, pattern):
        self.pattern = pattern
        super(The, self).__init__()

    def __str__(self):
        return self.pattern

    def at(self, at):
        """Anchor filter by converting all patterns to be absolute.
        """
        self.pattern = absname(self.pattern, at)
        return self

    def set(self, pattern):
        self.pattern = pattern

    def match(self, name, prefix=True):
        if match(name, self.pattern, prefix=prefix):
            return True
