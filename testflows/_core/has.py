# Copyright 2020 Katteli Inc.
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
import re
import operator

from .flags import Flags

class Filter:
    """Base filter.
    """
    def __init__(self, _op=None):
        self._op = _op

    def __call__(self, test):
        if self._op:
            return self._op(test)
        return True

    def __or__(self, other):
        def op(test):
            return operator.or_(self(test), other(test))
        return Filter(_op=op)

    def __and__(self, other):
        def op(test):
            return operator.and_(self(test), other(test))
        return Filter(_op=op)

    def __invert__(self):
        def op(test):
            return operator.not_(self(test))
        return Filter(_op=op)

class StringFilter(Filter):
    """Generic filter for string types.
    """
    parameter = None

    def __init__(self, s):
        self.s = s

    @classmethod
    def getattr(cls, test):
        return [getattr(p, cls.__name__) for p in getattr(test, cls.parameter, [])]

    @classmethod
    def startingwith(cls, s):
        def op(test):
            return len([a for a in cls.getattr(test) if a.startswith(s)]) > 0
        return Filter(_op=op)

    @classmethod
    def endingwith(cls, s):
        def op(test):
            return len([a for a in cls.getattr(test) if a.endswith(s)]) > 0
        return Filter(_op=op)

    @classmethod
    def containing(cls, s):
        def op(test):
            return len([a for a in cls.getattr(test) if s in a]) > 0
        return Filter(_op=op)

    @classmethod
    def matching(cls, pattern):
        pattern = re.compile(pattern)
        def op(test):
            return len([a for a in cls.getattr(test) if pattern.match(a)]) > 0
        return Filter(_op=op)

    def __call__(self, test):
        return self.s in self.getattr(test)


class has:
    """Class that contains filters that can be used
    to filter tests by their `name`, `flags`, `tags`,
    `attributes` and `requirements`.
    """
    class tag(StringFilter):
        """Test tag filter.
        """
        @staticmethod
        def getattr(test):
            return getattr(test, "tags", set())

    class name(StringFilter):
        """Test name filter.
        """
        @staticmethod
        def getattr(test):
            return [getattr(test, "name")]

    class flag(Filter):
        """Test flag filter.
        """
        def __init__(self, flag):
            self.flag = Flags(flag)

        def __call__(self, test):
            return self.flag in Flags(getattr(test, "flags", None))

    class attribute:
        """Test attribute filter.
        """
        class BaseFilter(StringFilter):
            parameter = "attributes"

        class name(BaseFilter):
            """Test attribute name filter.
            """
            pass

        class uid(BaseFilter):
            """Test attribute uid filter.
            """
            pass

        class value(BaseFilter):
            """Test attribute value filter.
            """
            pass

        class type(BaseFilter):
            """Test attribute type filter.
            """
            pass

        class group(BaseFilter):
            """Test attribute group filter.
            """
            pass

    class requirement:
        """Test requirement filter.
        """

        class BaseFilter(StringFilter):
            parameter = "requirements"

        class name(BaseFilter):
            """Test requirement name filter.
            """
            pass

        class uid(BaseFilter):
            """Test requirement uid filter.
            """
            pass

        class version(BaseFilter):
            """Test requirement version filter.
            """
            pass

        class priority(BaseFilter):
            """Test requirement group filter.
            """
            pass

        class type(BaseFilter):
            """Test requirement type filter.
            """
            pass

        class group(BaseFilter):
            """Test requirement group filter.
            """
            pass
