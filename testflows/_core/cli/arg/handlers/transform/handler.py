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
from testflows._core.cli.arg.common import epilog
from testflows._core.cli.arg.common import HelpFormatter
from testflows._core.cli.arg.handlers.handler import Handler as HandlerBase
from testflows._core.cli.arg.handlers.transform.nice import Handler as nice_handler
from testflows._core.cli.arg.handlers.transform.brisk import Handler as brisk_handler
from testflows._core.cli.arg.handlers.transform.short import Handler as short_handler
from testflows._core.cli.arg.handlers.transform.dots import Handler as dots_handler
from testflows._core.cli.arg.handlers.transform.compact import Handler as compact_handler
from testflows._core.cli.arg.handlers.transform.slick import Handler as slick_handler
from testflows._core.cli.arg.handlers.transform.classic import Handler as classic_handler
from testflows._core.cli.arg.handlers.transform.manual import Handler as manual_handler
from testflows._core.cli.arg.handlers.transform.fails import Handler as fails_handler
from testflows._core.cli.arg.handlers.transform.raw import Handler as raw_handler
from testflows._core.cli.arg.handlers.transform.compress import Handler as compress_handler
from testflows._core.cli.arg.handlers.transform.decompress import Handler as decompress_handler

class Handler(HandlerBase):
    @classmethod
    def add_command(cls, commands):
        parser = commands.add_parser("transform", help="log file transformation", epilog=epilog(),
            description="Transform log files.",
            formatter_class=HelpFormatter)

        transform_commands = parser.add_subparsers(title="commands", metavar="command",
            description=None, help=None)
        transform_commands.required = True
        raw_handler.add_command(transform_commands)
        nice_handler.add_command(transform_commands)
        brisk_handler.add_command(transform_commands)
        short_handler.add_command(transform_commands)
        slick_handler.add_command(transform_commands)
        classic_handler.add_command(transform_commands)
        manual_handler.add_command(transform_commands)
        fails_handler.add_command(transform_commands)
        dots_handler.add_command(transform_commands)
        compact_handler.add_command(transform_commands)
        compress_handler.add_command(transform_commands)
        decompress_handler.add_command(transform_commands)
