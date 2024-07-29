# Copyright 2024 Katteli Inc.
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
from testflows._core.cli.arg.common import epilog
from testflows._core.cli.arg.common import HelpFormatter
from testflows._core.cli.arg.handlers.handler import Handler as HandlerBase
from testflows._core.cli.arg.handlers.ssl.new import (
    Handler as new_handler,
)
from testflows._core.cli.arg.handlers.ssl.show import (
    Handler as show_handler,
)


class Handler(HandlerBase):
    @classmethod
    def add_command(cls, commands):
        parser = commands.add_parser(
            "ssl",
            help="ssl configuration",
            epilog=epilog(),
            description="SSL configuration.",
            formatter_class=HelpFormatter,
        )

        ssl_commands = parser.add_subparsers(
            title="commands", metavar="command", description=None, help=None
        )
        ssl_commands.required = True
        new_handler.add_command(ssl_commands)
        show_handler.add_command(ssl_commands)
