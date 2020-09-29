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
import subprocess
import tempfile

import testflows._core.cli.arg.type as argtype

from testflows._core.cli.arg.common import epilog
from testflows._core.cli.arg.common import HelpFormatter
from testflows._core.cli.arg.handlers.handler import Handler as HandlerBase
from testflows._core.message import Message
from testflows._core.transform.log.pipeline import Pipeline as PipelineBase
from testflows._core.transform.log.read_and_filter import transform as read_and_filter_transform
from testflows._core.transform.log.nice import transform as nice_transform
from testflows._core.transform.log.raw import transform as raw_transform
from testflows._core.transform.log.short import transform as short_transform
from testflows._core.transform.log.slick import transform as slick_transform
from testflows._core.transform.log.parse import transform as parse_transform
from testflows._core.transform.log.write import transform as write_transform

class Handler(HandlerBase):
    @classmethod
    def add_command(cls, commands):
        parser = commands.add_parser("messages", help="messages", epilog=epilog(),
            description="Show messages.",
            formatter_class=HelpFormatter)

        parser.add_argument("name", metavar="name", type=str, help="test name", default="")
        parser.add_argument("--log", metavar="input", type=argtype.logfile("r", bufsize=1, encoding="utf-8"),
                nargs="?", help="input log, default: stdin", default="-")
        parser.add_argument("--output", metavar="output", type=argtype.file("w", bufsize=1, encoding="utf-8"),
                nargs="?", help='output, default: stdout', default="-")
        format_choices = ["nice", "raw", "short", "slick"]
        parser.add_argument("--format", "-f", metavar="name", type=str, choices=format_choices,
            default="nice", help=f"output format, choices are {format_choices}, default: nice")
        parser.set_defaults(func=cls())

    class Pipeline(PipelineBase):
        def __init__(self, name, input, output, format=None, tail=False):
            stop_event = threading.Event()

            command = f"grep -E \',\"test_id\":\"%s'" % name
            steps = [
                read_and_filter_transform(input, command=command, tail=tail)
            ]
            if format == "nice":
                steps += [
                    parse_transform(stop_event),
                    nice_transform()
                ]
            elif format == "short":
                steps += [
                    parse_transform(stop_event),
                    short_transform()
                ]
            elif format == "slick":
                steps += [
                    parse_transform(stop_event),
                    slick_transform()
                ]
            steps.append(write_transform(output))

            super(Handler.Pipeline, self).__init__(steps)

    def convert_name_to_id(self, name, input):
        command = "grep --byte-offset -E '^{\"message_keyword\":\"%s\"" % Message.TEST.name
        command += ".+\"test_name\":\"%s\"' -m 1" % name.replace("'", r"'\''")
        process = subprocess.Popen(command, stdin=input, stdout=subprocess.PIPE, shell=True)
        process.wait()
        parse_generator = parse_transform(None)
        parse_generator.send(None)
        line = process.stdout.readline().decode("utf-8")
        if not line:
            raise ValueError("test not found")
        offset, msg = line.split(":", 1)
        return (parse_generator.send(msg)["test_id"], offset)

    def handle(self, args):
        try:
            with tempfile.NamedTemporaryFile("w+") as saved_input:
                saved_input.write(args.log.read())
                saved_input.seek(0)
                id, offset = self.convert_name_to_id(args.name, saved_input)
                saved_input.seek(int(offset))
                self.Pipeline(id, saved_input, args.output, args.format).run()
        except ValueError as exc:
            if "test not found" in str(exc):
                return
