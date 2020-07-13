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
from testflows._core.cli.arg.handlers.report.compare.command import Handler as HandlerBase
from testflows._core.cli.arg.handlers.report.compare.command import Formatter as FormatterBase
from testflows._core.cli.arg.handlers.report.compare.command import template

class Formatter(FormatterBase):
    def format(self, data):
        body = self.format_metadata(data)
        body += self.format_reference(data)
        body += self.format_chart(data)
        body += self.format_table(data)
        return template.strip() % {
            "title": "Results",
            "logo": self.format_logo(data),
            "confidential": self.format_confidential(data),
            "copyright": self.format_copyright(data),
            "body": body
        }

class Handler(HandlerBase):
    Formatter = Formatter

    @classmethod
    def add_command(cls, commands):
        parser = commands.add_parser("results", help="results report", epilog=epilog(),
            description="Generate results comparison report.",
            formatter_class=HelpFormatter)
        cls.add_arguments(parser)
        parser.set_defaults(func=cls())
