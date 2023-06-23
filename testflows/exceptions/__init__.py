# Copyright 2019-2022 Katteli Inc.
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
import sys
import traceback


def exception(exc_type=None, exc_value=None, exc_traceback=None):
    """Get exception string."""
    if (exc_type, exc_value, exc_traceback) == (None, None, None):
        exc_type, exc_value, exc_traceback = sys.exc_info()
    return "".join(
        traceback.format_exception(exc_type, exc_value, exc_traceback)
    ).rstrip()


class TestFlowsException(Exception):
    """Base exception class."""

    pass


class ResultException(TestFlowsException):
    """Result exception."""

    pass


class DummyTestException(TestFlowsException):
    """Dummy test exception."""

    pass


class TestIteration(TestFlowsException):
    """Repeat test."""

    def __init__(self, repeat, retry, *args, **kwargs):
        self.repeat = repeat
        self.retry = retry
        super(TestIteration, self).__init__(*args, **kwargs)


class TestRerunIndividually(TestFlowsException):
    """Repeat tests individually."""

    def __init__(self, tests, *args, **kwargs):
        self.tests = tests
        super(TestRerunIndividually, self).__init__(*args, **kwargs)


class TestFlowsError(TestFlowsException):
    """Base error exception class."""

    pass


class RequirementError(TestFlowsError):
    """Requirement error."""

    pass


class SpecificationError(TestFlowsError):
    """Specification error."""

    pass


class DescriptionError(TestFlowsError):
    """Description error."""

    pass


class ArgumentError(TestFlowsError):
    """Argument error."""

    pass


class TerminatedError(TestFlowsError):
    """Terminated error."""

    pass


class ExecutorError(TestFlowsError):
    """Executor error."""

    pass


class ExecutorWorkerError(ExecutorError):
    """Executor worker error."""

    pass
