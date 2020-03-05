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
import threading

from testflows._core.message import Message, ResultMessages
from testflows._core.testtype import TestType
from .read import transform as read_transform
from .parse import transform as parse_transform
from .nice import transform as nice_transform
from .dots import transform as dots_transform
from .write import transform as write_transform
from .stop import transform as stop_transform
from .raw import transform as raw_transform
from .short import transform as short_transform
from .slick import transform as slick_transform
from .index import transform as index_transform
from .read_and_filter import transform as read_and_filter_transform
from .report.passing import transform as passing_report_transform
from .report.fails import transform as fails_report_transform
from .report.totals import transform as totals_report_transform
from .report.version import transform as version_report_transform
from .report.results import transform as results_transform
from .report.map import transform as map_transform

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
            read_transform(input, tail=tail),
            raw_transform(stop_event),
            write_transform(output),
            stop_transform(stop_event)
        ]
        super(RawLogPipeline, self).__init__(steps)

class ShortLogPipeline(Pipeline):
    def __init__(self, input, output, tail=False):
        stop_event = threading.Event()

        steps = [
            read_transform(input, tail=tail),
            parse_transform(stop_event),
            fanout(
                short_transform(),
                passing_report_transform(stop_event),
                fails_report_transform(stop_event),
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
            read_transform(input, tail=tail),
            parse_transform(stop_event),
            fanout(
                nice_transform(stop_event),
                passing_report_transform(stop_event),
                fails_report_transform(stop_event),
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
            read_transform(input, tail=tail),
            parse_transform(stop_event),
            fanout(
                slick_transform(),
                passing_report_transform(stop_event),
                fails_report_transform(stop_event),
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

class DotsLogPipeline(Pipeline):
    def __init__(self, input, output, tail=False):
        stop_event = threading.Event()

        steps = [
            read_transform(input, tail=tail),
            parse_transform(stop_event),
            fanout(
                dots_transform(stop_event),
                passing_report_transform(stop_event),
                fails_report_transform(stop_event),
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

class TotalsReportLogPipeline(Pipeline):
    def __init__(self, input, output):
        stop_event = threading.Event()

        message_types = [Message.TEST] + ResultMessages
        command = f"grep -E '^({'|'.join([str(int(i)) for i in message_types])}),'"

        steps = [
            read_and_filter_transform(input, command=command),
            parse_transform(stop_event),
            fanout(
                totals_report_transform(stop_event),
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

        message_types = [Message.TEST] + ResultMessages
        command = f"grep -E '^({'|'.join([str(int(i)) for i in message_types])}),'"

        steps = [
            read_and_filter_transform(input, command=command),
            parse_transform(stop_event),
            fanout(
                fails_report_transform(stop_event),
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

        message_types = [Message.TEST] + ResultMessages
        command = f"grep -E '^({'|'.join([str(int(i)) for i in message_types])}),'"

        steps = [
            read_and_filter_transform(input, command=command),
            parse_transform(stop_event),
            fanout(
                passing_report_transform(stop_event),
            ),
            fanin(
                "".join
            ),
            write_transform(output),
            stop_transform(stop_event)
        ]
        super(PassingReportLogPipeline, self).__init__(steps)

class VersionReportLogPipeline(Pipeline):
    def __init__(self, input, output):
        stop_event = threading.Event()

        message_types = [Message.VERSION] + ResultMessages
        command = f"grep -E '^({'|'.join([str(int(i)) for i in message_types])}),'"

        steps = [
            read_and_filter_transform(input, command=command),
            parse_transform(stop_event),
            fanout(
                version_report_transform(stop_event),
            ),
            fanin(
                "".join
            ),
            write_transform(output),
            stop_transform(stop_event)
        ]
        super(VersionReportLogPipeline, self).__init__(steps)

class MapLogPipeline(Pipeline):
    def __init__(self, input, maps):
        stop_event = threading.Event()
        message_types = [Message.TEST]
        command = f"grep -m1 -E '^({'|'.join([str(int(i)) for i in message_types])}),'"

        steps = [
            read_and_filter_transform(input, command=command),
            parse_transform(stop_event),
            map_transform(maps, stop_event),
            stop_transform(stop_event)
        ]
        super(MapLogPipeline, self).__init__(steps)

class ResultsLogPipeline(Pipeline):
    def __init__(self, input, results):
        stop_event = threading.Event()
        message_types = [Message.VERSION, Message.TEST] + ResultMessages
        command = f"grep -E '^({'|'.join([str(int(i)) for i in message_types])}),'"

        steps = [
            read_and_filter_transform(input, command=command),
            parse_transform(stop_event),
            results_transform(results, stop_event),
            stop_transform(stop_event)
        ]
        super(ResultsLogPipeline, self).__init__(steps)

class CompactRawLogPipeline(Pipeline):
    def __init__(self, input, output, steps=True):
        stop_event = threading.Event()
        message_types = [Message.VERSION, Message.TEST] + ResultMessages
        test_types = [TestType.Module, TestType.Suite, TestType.Test]
        command = (f"grep -E '^({'|'.join([str(int(i)) for i in message_types])}),"
            + (f"\"[^\"]+\",[0-9]+,({'|'.join([str(t) for t in test_types])})," if not steps else "")
            + "'")

        steps = [
            read_and_filter_transform(input, command=command),
            raw_transform(stop_event),
            write_transform(output),
            stop_transform(stop_event)
        ]
        super(CompactRawLogPipeline, self).__init__(steps)

class IndexLogPipeline(Pipeline):
    def __init__(self, input, output):
        stop_event = threading.Event()

        steps = [
            read_and_filter_transform(input, command=f"grep -E '^{Message.TEST},'"),
            index_transform(stop_event),
            write_transform(output),
            stop_transform(stop_event)
        ]
        super(IndexLogPipeline, self).__init__(steps)
