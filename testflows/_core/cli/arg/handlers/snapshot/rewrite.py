# Copyright 2023 Katteli Inc.
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
from testflows._core.cli.text import secondary
from testflows._core.cli.arg.common import epilog
from testflows._core.cli.arg.common import HelpFormatter
from testflows._core.cli.arg.handlers.handler import Handler as HandlerBase
from testflows.asserts.helpers import rewrite_snapshot


class Handler(HandlerBase):
    @classmethod
    def add_command(cls, commands):
        parser = commands.add_parser(
            "rewrite",
            help="rewrite snapshot",
            epilog=epilog(),
            description=(
                "Rewrite snapshot files.\n\n"
                "For example:\n"
                "  tfs snapshots rewrite *.snapshot"
            ),
            formatter_class=HelpFormatter,
        )

        parser.add_argument(
            "input",
            metavar="input",
            type=str,
            nargs="+",
            help="input file or files",
        )

        parser.set_defaults(func=cls())

    def handle(self, args):
        for filename in args.input:
            try:
                rewrite_snapshot(filename)
            except ValueError as exc:
                print(secondary(f"skipping: {exc}", eol=""), file=sys.stderr)
            else:
                print(secondary(f"rewrote: {filename}", eol=""))
