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
import os
import datetime
import testflows._core.cli.arg.type as argtype

from testflows._core.cli.arg.common import epilog
from testflows._core.cli.arg.common import HelpFormatter
from testflows._core.cli.arg.handlers.handler import Handler as HandlerBase

class Handler(HandlerBase):
    @classmethod
    def add_command(cls, commands):
        parser = commands.add_parser("requirements", help="software requirements specification", epilog=epilog(),
            description="Create new software requirements specification document.",
            formatter_class=HelpFormatter)

        parser.add_argument("output", metavar="output", type=argtype.file("w", bufsize=1, encoding="utf-8"),
            nargs="?", help='output file, default: stdout', default="-")
        parser.add_argument("--number", metavar="number", type=str, help="document number", default="001")
        parser.add_argument("--title", metavar="name", type=str, help="document title", default="Template")
        parser.add_argument("--author", metavar="name", type=str, help="name of the author", default="*[author]*")
        parser.add_argument("--date", metavar="date", type=str, help="document date", default=f"{datetime.datetime.now():%B %d, %Y}")
        parser.set_defaults(func=cls())

    def handle(self, args):
        template_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "document", "new")

        with open(os.path.join(template_dir, "requirements.md")) as fd:
            template = fd.read()

        args.output.write(template.format(
            number=args.number,
            title=args.title,
            author=args.author,
            date=args.date))