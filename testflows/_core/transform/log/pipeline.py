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
import threading

from testflows._core.message import Message
from testflows._core.testtype import TestType
from .read import transform as read_transform
from .read_raw import transform as read_raw_transform
from .parse import transform as parse_transform
from .nice import transform as nice_transform
from .dots import transform as dots_transform
from .write import transform as write_transform
from .stop import transform as stop_transform
from .raw import transform as raw_transform
from .short import transform as short_transform
from .slick import transform as slick_transform
from .classic import transform as classic_transform
from .fails import transform as fails_transform
from .read_and_filter import transform as read_and_filter_transform
from .report.passing import transform as passing_report_transform
from .report.fails import transform as fails_report_transform
from .report.totals import transform as totals_report_transform
from .report.version import transform as version_report_transform
from .report.coverage import transform as coverage_report_transform
from .report.metrics import transform as metrics_transform
from .report.results import transform as results_transform

class Pipeline(object):
    """Combines multiple steps into a pipeline
    that can be executed.
    """
    def __init__(self, steps):
        self.steps = steps
        # start all the generators
        for step in self.steps:
            next(step)

    def run(self):
        """Execute pipeline.
        """
        item = None
        while True:
            try:
                for step in self.steps:
                    item = step.send(item)
                    if item is None:
                        break
            except StopIteration:
                break

def fanout(*steps):
    """Single step of pipeline
    that feeds the same input to
    multiple steps and produces
    a list of outputs from each step.

    :param *steps: fan out steps
    """
    item = None
    outputs = []
    while True:
        for step in steps:
            output = step.send(item)
            if output is not None:
                outputs.append(output)
        item = yield outputs or None
        outputs = []

def fanin(combinator):
    """Combine multiple outputs into one.
    using the combinator
    """
    item = None
    while True:
        if item is not None:
            item = combinator(item)
        item = yield item

class RawLogPipeline(Pipeline):
    def __init__(self, input, output, tail=False):
        stop_event = threading.Event()

        steps = [
            read_transform(input, tail=tail, stop=stop_event),
            raw_transform(),
            write_transform(output),
            stop_transform(stop_event)
        ]
        super(RawLogPipeline, self).__init__(steps)

class ReadRawLogPipeline(Pipeline):
    def __init__(self, input, output, encoding=None):
        stop_event = threading.Event()

        steps = [
            read_raw_transform(input, stop=stop_event, encoding=encoding),
            write_transform(output),
            stop_transform(stop_event)
        ]
        super(ReadRawLogPipeline, self).__init__(steps)

class ShortLogPipeline(Pipeline):
    def __init__(self, input, output, tail=False):
        stop_event = threading.Event()

        steps = [
            read_transform(input, tail=tail, stop=stop_event),
            parse_transform(stop_event),
            fanout(
                short_transform(),
                passing_report_transform(stop_event),
                fails_report_transform(stop_event),
                coverage_report_transform(stop_event),
                totals_report_transform(stop_event),
                version_report_transform(stop_event),
            ),
            fanin(
                "".join
            ),
            write_transform(output),
            stop_transform(stop_event)
        ]
        super(ShortLogPipeline, self).__init__(steps)

class NiceLogPipeline(Pipeline):
    def __init__(self, input, output, tail=False):
        stop_event = threading.Event()

        steps = [
            read_transform(input, tail=tail, stop=stop_event),
            parse_transform(stop_event),
            fanout(
                nice_transform(),
                passing_report_transform(stop_event),
                fails_report_transform(stop_event),
                coverage_report_transform(stop_event),
                totals_report_transform(stop_event),
                version_report_transform(stop_event),
            ),
            fanin(
                "".join
            ),
            write_transform(output),
            stop_transform(stop_event)
        ]
        super(NiceLogPipeline, self).__init__(steps)

class SlickLogPipeline(Pipeline):
    def __init__(self, input, output, tail=False):
        stop_event = threading.Event()

        steps = [
            read_transform(input, tail=tail, stop=stop_event),
            parse_transform(stop_event),
            fanout(
                slick_transform(),
                passing_report_transform(stop_event),
                fails_report_transform(stop_event),
                coverage_report_transform(stop_event),
                totals_report_transform(stop_event),
                version_report_transform(stop_event),
            ),
            fanin(
                "".join
            ),
            write_transform(output),
            stop_transform(stop_event)
        ]
        super(SlickLogPipeline, self).__init__(steps)

class ClassicLogPipeline(Pipeline):
    def __init__(self, input, output, tail=False):
        stop_event = threading.Event()

        steps = [
            read_transform(input, tail=tail, stop=stop_event),
            parse_transform(stop_event),
            fanout(
                classic_transform(),
                passing_report_transform(stop_event),
                fails_report_transform(stop_event),
                coverage_report_transform(stop_event),
                totals_report_transform(stop_event),
                version_report_transform(stop_event),
            ),
            fanin(
                "".join
            ),
            write_transform(output),
            stop_transform(stop_event)
        ]
        super(ClassicLogPipeline, self).__init__(steps)

class FailsLogPipeline(Pipeline):
    def __init__(self, input, output, tail=False, only_new=False):
        stop_event = threading.Event()

        steps = [
            read_transform(input, tail=tail, stop=stop_event),
            parse_transform(stop_event),
            fanout(
                fails_transform(only_new=only_new),
                fails_report_transform(stop_event, only_new=only_new),
                coverage_report_transform(stop_event),
                totals_report_transform(stop_event),
                version_report_transform(stop_event),
            ),
            fanin(
                "".join
            ),
            write_transform(output),
            stop_transform(stop_event)
        ]
        super(FailsLogPipeline, self).__init__(steps)

class DotsLogPipeline(Pipeline):
    def __init__(self, input, output, tail=False):
        stop_event = threading.Event()

        steps = [
            read_transform(input, tail=tail, stop=stop_event),
            parse_transform(stop_event),
            fanout(
                dots_transform(stop_event),
                passing_report_transform(stop_event),
                fails_report_transform(stop_event),
                coverage_report_transform(stop_event),
                totals_report_transform(stop_event),
                version_report_transform(stop_event),
            ),
            fanin(
                "".join
            ),
            write_transform(output),
            stop_transform(stop_event)
        ]
        super(DotsLogPipeline, self).__init__(steps)

class MetricsLogPipeline(Pipeline):
    def __init__(self, input, metrics):
        stop_event = threading.Event()

        message_types = [Message.METRIC.name, Message.STOP.name]
        grep = "grep -E '^{\"message_keyword\":\""
        command = f"{grep}({'|'.join(message_types)})\"'"

        steps = [
            read_and_filter_transform(input, command=command, stop=stop_event),
            parse_transform(),
            metrics_transform(metrics),
            stop_transform(stop_event)
        ]
        super(MetricsLogPipeline, self).__init__(steps)

class ResultsReportLogPipeline(Pipeline):
    def __init__(self, input, output):
        stop_event = threading.Event()

        message_types = [Message.TEST.name, Message.RESULT.name, Message.STOP.name]
        grep = "grep -E '^{\"message_keyword\":\""
        command = f"{grep}({'|'.join(message_types)})\"'"

        steps = [
            read_and_filter_transform(input, command=command, stop=stop_event),
            parse_transform(),
            fanout(
                passing_report_transform(stop_event),
                fails_report_transform(stop_event),
                coverage_report_transform(stop_event),
                totals_report_transform(stop_event),
                version_report_transform(stop_event)
            ),
            fanin(
                "".join
            ),
            write_transform(output),
            stop_transform(stop_event)
        ]
        super(ResultsReportLogPipeline, self).__init__(steps)

class TotalsReportLogPipeline(Pipeline):
    def __init__(self, input, output):
        stop_event = threading.Event()

        message_types = [Message.TEST.name, Message.RESULT.name, Message.STOP.name]
        grep = "grep -E '^{\"message_keyword\":\""
        command = f"{grep}({'|'.join(message_types)})\"'"

        steps = [
            read_and_filter_transform(input, command=command, stop=stop_event),
            parse_transform(),
            fanout(
                totals_report_transform(stop_event, divider=""),
            ),
            fanin(
                "".join
            ),
            write_transform(output),
            stop_transform(stop_event)
        ]
        super(TotalsReportLogPipeline, self).__init__(steps)

class FailsReportLogPipeline(Pipeline):
    def __init__(self, input, output):
        stop_event = threading.Event()

        message_types = [Message.RESULT.name, Message.STOP.name]
        grep = "grep -E '^{\"message_keyword\":\""
        command = f"{grep}({'|'.join(message_types)})\"'"

        steps = [
            read_and_filter_transform(input, command=command, stop=stop_event),
            parse_transform(),
            fanout(
                fails_report_transform(stop_event, divider=""),
            ),
            fanin(
                "".join
            ),
            write_transform(output),
            stop_transform(stop_event)
        ]
        super(FailsReportLogPipeline, self).__init__(steps)

class PassingReportLogPipeline(Pipeline):
    def __init__(self, input, output):
        stop_event = threading.Event()

        message_types = [Message.RESULT.name, Message.STOP.name]
        grep = "grep -E '^{\"message_keyword\":\""
        command = f"{grep}({'|'.join(message_types)})\"'"
        steps = [
            read_and_filter_transform(input, command=command, stop=stop_event),
            parse_transform(),
            fanout(
                passing_report_transform(stop_event, divider=""),
            ),
            fanin(
                "".join
            ),
            write_transform(output),
            stop_transform(stop_event)
        ]
        super(PassingReportLogPipeline, self).__init__(steps)

class CoverageReportLogPipeline(Pipeline):
    def __init__(self, input, output):
        stop_event = threading.Event()

        message_types = [Message.TEST.name, Message.RESULT.name, Message.REQUIREMENT.name, Message.SPECIFICATION.name, Message.STOP.name]
        grep = "grep -E '^{\"message_keyword\":\""
        command = f"{grep}({'|'.join(message_types)})\"'"

        steps = [
            read_and_filter_transform(input, command=command, stop=stop_event),
            parse_transform(),
            fanout(
                coverage_report_transform(stop_event, divider=""),
            ),
            fanin(
                "".join
            ),
            write_transform(output),
            stop_transform(stop_event)
        ]
        super(CoverageReportLogPipeline, self).__init__(steps)

class VersionReportLogPipeline(Pipeline):
    def __init__(self, input, output):
        stop_event = threading.Event()

        message_types = [Message.VERSION.name, Message.STOP.name]
        grep = "grep -m2 -E '^{\"message_keyword\":\""
        command = f"{grep}({'|'.join(message_types)})\"'"
        steps = [
            read_and_filter_transform(input, command=command, stop=stop_event),
            parse_transform(),
            fanout(
                version_report_transform(stop_event, divider=""),
            ),
            fanin(
                "".join
            ),
            write_transform(output),
            stop_transform(stop_event)
        ]
        super(VersionReportLogPipeline, self).__init__(steps)

class ResultsLogPipeline(Pipeline):
    def __init__(self, input, results, steps=True):
        stop_event = threading.Event()
        message_types = [
            Message.PROTOCOL.name,
            Message.VERSION.name,
            Message.TEST.name,
            Message.RESULT.name,
            Message.MAP.name,
            Message.NODE.name,
            Message.ATTRIBUTE.name,
            Message.TAG.name,
            Message.ARGUMENT.name,
            Message.REQUIREMENT.name,
            Message.EXAMPLE.name,
            Message.TICKET.name,
            Message.VALUE.name,
            Message.METRIC.name,
            Message.STOP.name
        ]
        test_types = [TestType.Module.name, TestType.Suite.name, TestType.Test.name]
        command = "grep -E '^{\"message_keyword\":\""
        command = (f"{command}({'|'.join(message_types)})\""
            + ((".+\"test_type\":\"" + f"({'|'.join(test_types)})\"") if not steps else "")
            + "'")
        steps = [
            read_and_filter_transform(input, command=command, stop=stop_event),
            parse_transform(stop_event),
            results_transform(results),
            stop_transform(stop_event)
        ]
        super(ResultsLogPipeline, self).__init__(steps)

class CompactRawLogPipeline(Pipeline):
    def __init__(self, input, output, steps=True):
        stop_event = threading.Event()
        message_types = [
            Message.PROTOCOL.name,
            Message.VERSION.name,
            Message.TEST.name,
            Message.RESULT.name,
            Message.MAP.name,
            Message.NODE.name,
            Message.ATTRIBUTE.name,
            Message.TAG.name,
            Message.ARGUMENT.name,
            Message.REQUIREMENT.name,
            Message.EXAMPLE.name,
            Message.TICKET.name,
            Message.VALUE.name,
            Message.METRIC.name,
            Message.STOP.name
        ]
        test_types = [TestType.Module.name, TestType.Suite.name, TestType.Test.name]
        command = "grep -E '^{\"message_keyword\":\""
        command = (f"{command}({'|'.join(message_types)})\""
            + ((".+\"test_type\":\"" + f"({'|'.join(test_types)})\"") if not steps else "")
            + "'")
        steps = [
            read_and_filter_transform(input, command=command, stop=stop_event),
            raw_transform(),
            write_transform(output),
            stop_transform(stop_event)
        ]
        super(CompactRawLogPipeline, self).__init__(steps)
