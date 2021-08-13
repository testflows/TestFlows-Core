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
from testflows._core.cli.arg.handlers.show.passing import Handler as passing_handler
from testflows._core.cli.arg.handlers.show.totals import Handler as totals_handler
from testflows._core.cli.arg.handlers.show.fails import Handler as fails_handler
from testflows._core.cli.arg.handlers.show.unstable import Handler as unstable_handler
from testflows._core.cli.arg.handlers.show.version import Handler as version_handler
from testflows._core.cli.arg.handlers.show.coverage import Handler as coverage_handler
from testflows._core.cli.arg.handlers.show.results import Handler as results_handler
from testflows._core.cli.arg.handlers.show.details import Handler as details_handler
from testflows._core.cli.arg.handlers.show.metrics import Handler as metrics_handler
from testflows._core.cli.arg.handlers.show.procedure import Handler as procedure_handler
from testflows._core.cli.arg.handlers.show.arguments import Handler as arguments_handler
from testflows._core.cli.arg.handlers.show.requirements import Handler as requirements_handler
from testflows._core.cli.arg.handlers.show.attributes import Handler as attributes_handler
from testflows._core.cli.arg.handlers.show.tags import Handler as tags_handler
from testflows._core.cli.arg.handlers.show.description import Handler as description_handler
from testflows._core.cli.arg.handlers.show.result import Handler as result_handler
from testflows._core.cli.arg.handlers.show.examples import Handler as examples_handler
from testflows._core.cli.arg.handlers.show.specifications import Handler as specifications_handler
from testflows._core.cli.arg.handlers.show.messages import Handler as messages_handler
from testflows._core.cli.arg.handlers.show.tests import Handler as tests_handler

class Handler(HandlerBase):
    @classmethod
    def add_command(cls, commands):
        parser = commands.add_parser("show", help="show test data", epilog=epilog(),
            description="Show test data.",
            formatter_class=HelpFormatter)

        show_commands = parser.add_subparsers(title="commands", metavar="command",
            description=None, help=None)
        show_commands.required = True
        results_handler.add_command(show_commands)
        passing_handler.add_command(show_commands)
        fails_handler.add_command(show_commands)
        unstable_handler.add_command(show_commands)
        totals_handler.add_command(show_commands)
        coverage_handler.add_command(show_commands)
        version_handler.add_command(show_commands)
        tests_handler.add_command(show_commands)
        messages_handler.add_command(show_commands)
        details_handler.add_command(show_commands)
        procedure_handler.add_command(show_commands)
        description_handler.add_command(show_commands)
        arguments_handler.add_command(show_commands)
        attributes_handler.add_command(show_commands)
        requirements_handler.add_command(show_commands)
        tags_handler.add_command(show_commands)
        metrics_handler.add_command(show_commands)
        examples_handler.add_command(show_commands)
        specifications_handler.add_command(show_commands)
        result_handler.add_command(show_commands)
