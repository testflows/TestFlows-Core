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
import tempfile
import testflows._core.cli.arg.type as argtype

from testflows._core.cli.arg.common import epilog
from testflows._core.cli.arg.common import HelpFormatter
from testflows._core.cli.arg.handlers.handler import Handler as HandlerBase
from testflows._core.document.toc import generate

class Handler(HandlerBase):
    @classmethod
    def add_command(cls, commands):
        parser = commands.add_parser("toc", help="generate table of contents", epilog=epilog(),
            description="Genarate table of contents for a document.",
            formatter_class=HelpFormatter)

        parser.add_argument("input", metavar="input", type=argtype.file("r", bufsize=1, encoding="utf-8"),
                nargs="?", help="input file, default: stdin", default="-")
        parser.add_argument("output", metavar="output", type=str,
                nargs="?", help='output file, default: stdout', default="-")

        parser.add_argument("--heading", metavar="name", type=str, default="Table of Contents",
                help="table of contents heading name, default: 'Table of Contents'")
        parser.add_argument("-u", "--update", action="store_true", default=False,
                help="output original document with an updated table of contents")

        parser.set_defaults(func=cls())

    def handle(self, args):
        with tempfile.TemporaryFile("w+", encoding="utf-8") as temporary_file:
            generate(args.input, temporary_file, args.heading, args.update)
            output = argtype.file("w", encoding="utf-8")(args.output)
            temporary_file.flush()
            temporary_file.seek(0)
            output.write(temporary_file.read())
            output.flush()