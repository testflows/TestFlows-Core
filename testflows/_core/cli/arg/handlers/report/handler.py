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
from testflows._core.cli.arg.handlers.report.srs_coverage import Handler as srs_coverage_handler
from testflows._core.cli.arg.handlers.report.results import Handler as results_handler
from testflows._core.cli.arg.handlers.report.compare.handler import Handler as compare_handler
from testflows._core.cli.arg.handlers.report.coverage import Handler as coverage_handler
from testflows._core.cli.arg.handlers.report.metrics import Handler as metrics_handler
from testflows._core.cli.arg.handlers.report.specification import Handler as specification_handler
from testflows._core.cli.arg.handlers.report.tracebility import Handler as tracebility_handler

class Handler(HandlerBase):
    @classmethod
    def add_command(cls, commands):
        parser = commands.add_parser("report", help="generate report", epilog=epilog(),
            description="Generate report.",
            formatter_class=HelpFormatter)

        report_commands = parser.add_subparsers(title="commands", metavar="command",
            description=None, help=None)
        report_commands.required = True
        results_handler.add_command(report_commands)
        specification_handler.add_command(report_commands)
        tracebility_handler.add_command(report_commands)
        coverage_handler.add_command(report_commands)
        compare_handler.add_command(report_commands)
        metrics_handler.add_command(report_commands)
        #srs_coverage_handler.add_command(report_commands)
