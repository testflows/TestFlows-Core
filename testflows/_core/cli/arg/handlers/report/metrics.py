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
import io
import csv
import testflows._core.cli.arg.type as argtype

from testflows._core.cli.arg.common import epilog
from testflows._core.cli.arg.common import HelpFormatter
from testflows._core.cli.arg.handlers.handler import Handler as HandlerBase
from testflows._core.transform.log.pipeline import MetricsLogPipeline
from testflows._core.message import dumps

class OpenMetricsFormatter:
    def format_metric_name(self, name):
        return name.replace(" ", "_")

    def format_metric(self, metric):
        metric_name = self.format_metric_name(metric["metric_name"])
        metric_value = metric["metric_value"]
        metric_units = metric["metric_units"]
        metric_time = metric["message_time"]
        test_name = metric["test_name"]

        return f"{metric_name}{{test={dumps(test_name)},units={dumps(metric_units)}}} {metric_value} {int(metric_time)}\n"

    def format(self, data):
        body = ""
        for metric in data["metrics"]:
             body += self.format_metric(metric)
        return body

class CSVMetricsFormatter:
    def format_metric_name(self, name):
        return name.replace(" ", "_")

    def format_metric(self, writer, metric):
        metric_name = self.format_metric_name(metric["metric_name"])
        metric_value = metric["metric_value"]
        metric_units = metric["metric_units"]
        metric_time = metric["message_time"]
        test_name = metric["test_name"]
        writer.writerow((test_name, metric_name, metric_units, metric_value, int(metric_time)))

    def format(self, data):
        body = io.StringIO()
        header = "test_name", "metric_name", "metric_units", "metric_value", "metric_time"
        writer = csv.writer(body, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(header)
        for metric in data["metrics"]:
             self.format_metric(writer, metric)
        return body.getvalue()


class Handler(HandlerBase):
    @classmethod
    def add_command(cls, commands):
        parser = commands.add_parser("metrics", help="metrics report", epilog=epilog(),
            description="Generate metrics report.",
            formatter_class=HelpFormatter)

        parser.add_argument("input", metavar="input", type=argtype.logfile("r", bufsize=1, encoding="utf-8"),
                nargs="?", help="input log, default: stdin", default="-")
        parser.add_argument("output", metavar="output", type=argtype.file("w", bufsize=1, encoding="utf-8"),
                nargs="?", help='output file, default: stdout', default="-")
        parser.add_argument("--format", metavar="type", type=str,
            help="output format choices: 'openmetrics', 'csv' default: openmetrics", choices=["openmetrics", "csv"], default="openmetrics")

        parser.set_defaults(func=cls())

    def data(self, metrics, args):
        d = dict()
        d["metrics"] = metrics
        return d

    def generate(self, formatter, metrics, args):
        output = args.output
        output.write(
            formatter.format(self.data(metrics, args))
        )

    def handle(self, args):
        metrics = []
        MetricsLogPipeline(args.input, metrics).run()
        if args.format == "openmetrics":
            formatter = OpenMetricsFormatter()
        elif args.format == "csv":
            formatter = CSVMetricsFormatter()
        self.generate(formatter, metrics, args)
