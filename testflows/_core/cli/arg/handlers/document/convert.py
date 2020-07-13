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
import testflows._core.cli.arg.type as argtype

from testflows._core.cli.arg.common import epilog
from testflows._core.cli.arg.common import HelpFormatter
from testflows._core.cli.arg.handlers.handler import Handler as HandlerBase
from testflows._core.document.convert import generate, stylesheet
from testflows._core.contrib.markdown2 import Markdown

class Handler(HandlerBase):
    @classmethod
    def add_command(cls, commands):
        parser = commands.add_parser("convert", help="convert document", epilog=epilog(),
            description="Convert markdown document.",
            formatter_class=HelpFormatter)

        parser.add_argument("input", metavar="input", type=argtype.file("r", bufsize=1, encoding="utf-8"),
            nargs="?", help="input file, default: stdin", default="-")
        parser.add_argument("output", metavar="output", type=argtype.file("w", bufsize=1, encoding="utf-8"),
            nargs="?", help='output file, default: stdout', default="-")
        parser.add_argument("-f", "--format", metavar="format", type=str, help="format, default: html",
            choices=["html"], default="html")
        parser.add_argument("-s", "--stylesheet", metavar="css", type=argtype.file("r", bufsize=1, encoding="utf-8"),
            help="custom stylesheet", default=stylesheet)

        parser.set_defaults(func=cls())

    def handle(self, args):
        generate(args.input, args.output, args.stylesheet, args.format)
