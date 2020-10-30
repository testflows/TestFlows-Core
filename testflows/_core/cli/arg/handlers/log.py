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
import glob
import tempfile

import testflows._core.cli.arg.type as argtype

from testflows._core.cli.arg.common import epilog
from testflows._core.cli.arg.common import HelpFormatter
from testflows._core.cli.arg.handlers.handler import Handler as HandlerBase
from testflows._core.templog import parser as templog_parser, dirname as templog_dirname, ppid_glob as templog_glob

class Handler(HandlerBase):
    @classmethod
    def add_command(cls, commands):
        parser = commands.add_parser("log", help="retrieve last temporary test log", epilog=epilog(),
            description="Retrieve last temporary test log.",
            formatter_class=HelpFormatter)

        parser.add_argument("output", metavar="output", type=argtype.file("wb"), help='output file, stdout: \'-\'')

        parser.set_defaults(func=cls())

    def handle(self, args):
        ppid = os.getppid()

        found = False

        for file in sorted(glob.glob(os.path.join(templog_dirname(), templog_glob(ppid))), reverse=True):
            match = templog_parser.match(file)
            if not match:
                continue

            found = True
            with argtype.file("rb")(file) as fd:
                args.output.write(fd.read())

            break

        if not found:
            raise FileNotFoundError("no test logs found")
