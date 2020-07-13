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
import datetime

from testflows._core.utils.format import bytesize
from testflows._core.cli.arg.common import epilog
from testflows._core.cli.arg.common import HelpFormatter
from testflows._core.cli.arg.handlers.report.compare.command import Handler as HandlerBase
from testflows._core.cli.arg.handlers.report.compare.command import Formatter as FormatterBase
from testflows._core.cli.arg.handlers.report.compare.command import template, testflows
from testflows._core.utils.timefuncs import localfromtimestamp, strftimedelta

class Formatter(FormatterBase):
    def format_metadata(self, data):
        metadata = data["metadata"]
        s = (
            "\n\n"
            f"||**Date**||{localfromtimestamp(metadata['date']):%b %d, %Y %-H:%M}||\n"
            f'||**Framework**||'
            f'{testflows} {metadata["version"]}||\n'
        )
        if metadata.get("metrics"):
            s += f'||**Metrics**||{", ".join(metadata["metrics"])}||\n'
        if metadata.get("order-by"):
            s += f'||**Order By**||{metadata["order-by"].capitalize()}||\n'
        if metadata.get("sort"):
            s += f'||**Sort**||{"Ascending" if metadata["sort"] == "asc" else "Descending"}||\n'
        if metadata.get("filter"):
            s += f'||**Filter**||{metadata["filter"]}||\n'
        return s + "\n"

    def format_table(self, data):
        table = data["table"]
        s = "\n\n## Comparison\n\n"
        # comparison table
        s += " | ".join(table["header"]) + "\n"
        s += " | ".join(["---"] * len(table["header"])) + "\n"
        span = '<span class="result result-%(cls)s">%(value)s</span>'
        for row in table["rows"]:
            name, *results = row
            s += " | ".join([name] + [
                span % {'cls': result["result_type"].lower() if result else 'na', 'value': table["value"](result) if result else '-'} for result in results
            ]) + "\n"
        return s

    def format_chart(self, data):
        return ""

    def format(self, data):
        body = self.format_metadata(data)
        body += self.format_reference(data)
        body += self.format_chart(data)
        body += self.format_table(data)
        return template.strip() % {
            "title": "Metrics",
            "logo": self.format_logo(data),
            "confidential": self.format_confidential(data),
            "copyright": self.format_copyright(data),
            "body": body
        }

class Handler(HandlerBase):
    Formatter = Formatter

    @classmethod
    def add_command(cls, commands):
        parser = commands.add_parser("metrics", help="metrics report", epilog=epilog(),
            description="Generate metrics comparison report.",
            formatter_class=HelpFormatter)
        cls.add_arguments(parser)
        parser.add_argument("--name", metavar="name", type=str,
            nargs="+", help="metrics name, default: test-time", default=["test-time"])
        parser.set_defaults(func=cls())

    def metadata(self, only, order_by, direction, metrics):
        m = super(Handler, self).metadata(only, order_by, direction)
        m["metrics"] = metrics
        return m

    def data(self, results, args):
        d = dict()
        results = self.sort(results, args.order_by, args.sort)
        d["tests"] = self.filter(self.tests(results), args.only)
        d["table"] = self.table(d["tests"], results, args.log_link)
        d["counts"] = self.counts(d["tests"], results)
        d["chart"] = self.chart(d["counts"])
        d["metadata"] = self.metadata(args.only, args.order_by, args.sort, args.name)
        d["company"] = self.company(args)

        def table_value(result):
            metrics = []
            for name in args.name:
                if name == "test-time":
                   metrics.append(strftimedelta(result["message_rtime"]))
                else:
                    for metric in result["metrics"]:
                        if metric["metric_name"] == name:
                            if metric["metric_units"] == "ms":
                                metrics.append(f'{(int(metric["metric_value"]) / 1000.0)}s')
                            elif metric["metric_units"] == "bytes":
                                metrics.append(f'{bytesize(int(metric["metric_value"]))}')
                            else:
                                metrics.append(f'{metric["metric_value"]} {metric["metric_units"]}')
            return str("<br>".join(metrics)) if metrics else "-"

        d["table"]["value"] = table_value
        return d
