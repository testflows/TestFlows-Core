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
import testflows._core.cli.arg.type as argtype

from testflows._core.message import Message
from testflows._core.cli.arg.common import epilog
from testflows._core.cli.arg.common import HelpFormatter
from testflows._core.cli.arg.handlers.handler import Handler as HandlerBase
from testflows._core.testtype import TestType
from testflows._core.transform.log.pipeline import Pipeline as PipelineBase
from testflows._core.transform.log.read_and_filter import transform as read_and_filter_transform
from testflows._core.transform.log.report.results import transform as results_transform
from testflows._core.transform.log.values import transform as values_transform
from testflows._core.transform.log.parse import transform as parse_transform
from testflows._core.transform.log.write import transform as write_transform

def test_details_transform():
    """Transform parsed log line into a short format.
    """
    test = None
    while True:
        line = None
        if test is not None:
            if getattr(TestType, test["test"]["test_type"]) >= TestType.Test:
                line = f"{test['test']['test_name']}\n"
        test = yield line

class Handler(HandlerBase):
    @classmethod
    def add_command(cls, commands):
        parser = commands.add_parser("details", help="details", epilog=epilog(),
            description="Show details.",
            formatter_class=HelpFormatter)

        parser.add_argument("--log", metavar="input", type=argtype.logfile("r", bufsize=1, encoding="utf-8"),
                nargs="?", help="input log, default: stdin", default="-")
        parser.add_argument("--output", metavar="output", type=argtype.file("w", bufsize=1, encoding="utf-8"),
                nargs="?", help='output, default: stdout', default="-")

        parser.set_defaults(func=cls())

    class FirstStage(PipelineBase):
        def __init__(self, results, input):
            stop_event = threading.Event()

            message_types = [Message.TEST.name]
            grep = "grep -E '^{\"message_keyword\":\""
            command = f"{grep}({'|'.join(message_types)})\"'"

            steps = [
                read_and_filter_transform(input, command=command),
                parse_transform(stop_event),
                results_transform(results),
            ]
            super(Handler.FirstStage, self).__init__(steps)

    class SecondStage(PipelineBase):
        def __init__(self, results, output):
            steps = [
                values_transform(results.values()),
                test_details_transform(),
                write_transform(output)
            ]
            super(Handler.SecondStage, self).__init__(steps)

    def handle(self, args):
        results = {}
        self.FirstStage(results, args.log).run()
        self.SecondStage(results["tests"], args.output).run()
