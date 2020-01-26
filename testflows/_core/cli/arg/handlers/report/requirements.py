# Copyright 2019 Vitaliy Zakaznikov (TestFlows Test Framework http://testflows.com)
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
import sys
import json
import time
import threading
import importlib.util

from datetime import datetime

import testflows.settings as settings
import testflows._core.cli.arg.type as argtype

from testflows._core import __version__
from testflows._core.flags import Flags, SKIP
from testflows._core.testtype import TestType
from testflows._core.transform.log.message import message_map
from testflows._core.cli.arg.common import epilog
from testflows._core.cli.arg.common import HelpFormatter
from testflows._core.cli.arg.handlers.handler import Handler as HandlerBase
from testflows._core.transform.log.pipeline import ResultsLogPipeline
from testflows._core.transform.log.message import FailResults, XoutResults
from testflows._core.utils.timefuncs import localfromtimestamp, strftimedelta
from testflows._core.filters import the
from testflows._core.name import sep
from testflows._core.transform.log.report.totals import Counts
from testflows._core.objects import Requirement

testflows = '<span class="testflows-logo"></span> [<span class="logo-test">Test</span><span class="logo-flows">Flows</span>]'
testflows_em = testflows.replace("[", "").replace("]", "")

template = f"""
# Requirements Coverage Report
%(body)s
  
---
Generated by {testflows} Open-Source Test Framework

[<span class="logo-test">Test</span><span class="logo-flows">Flows</span>]: https://testflows.com
[ClickHouse]: https://clickhouse.yandex


<script>
%(script)s
</script>

"""

script = """
    window.onload = function(){
        // Toggle requirement description on click
        document.querySelectorAll('.requirement').forEach(
            function(item){
                item.addEventListener('click', function(){
                    item.nextSibling.classList.toggle('show');
                    item.children[0].classList.toggle('active');    
                });
            });
    }
"""

class Formatter:
    utf_icons = {
        "satisfied": "\u2714",
        "unsatisfied": "\u2718",
        "untested": "\u270E"
    }

    icon_colors = {
        "satisfied": "color-ok",
        "unsatisfied": "color-fail",
        "untested": "color-error"
    }

    def format_metadata(self, data):
        metadata = data["metadata"]
        s = (
            "\n\n"
            f"||**Date**||{localfromtimestamp(metadata['date']):%b %d, %Y %-H:%M}||\n"
            f'||**Framework**||'
            f'{testflows} {metadata["version"]}||\n'
        )
        return s + "\n"

    def format_summary(self, data):
        counts = data["counts"]

        def template(value, title, color):
            return (
                f'<div class="c100 p{value} {color} smaller-title">'
                    f'<span>{value}%</span>'
                    f'<span class="title">{title}</span>'
                    '<div class="slice">'
                        '<div class="bar"></div>'
                        '<div class="fill"></div>'
                    '</div>'
                '</div>\n')

        s = "\n## Summary\n"
        if counts.units <= 0:
            s += "No tests"
        else:
            s += '<div class="chart">'
            if counts.satisfied > 0:
                s += template(f"{counts.satisfied / float(counts.units) * 100:.0f}", "Satisfied", "green")
            if counts.unsatisfied > 0:
                s += template(f"{counts.unsatisfied / float(counts.units) * 100:.0f}", "Unsatisfied", "red")
            if counts.untested > 0:
                s += template(f"{counts.untested / float(counts.units) * 100:.0f}", "Untested", "orange")
            s += '</div>\n'
        return s

    def format_statistics(self, data):
        counts = data["counts"]
        result_map = {
            "OK": "Satisfied",
            "Fail": "Unsatisfied",
            "Error": "Untested"
        }
        s = "\n\n## Statistics\n"
        s += "||" + "||".join(
            ["<span></span>", "Units"]
            + [f'<span class="result result-{k.lower()}">{v}</span>' for k, v in result_map.items()]
        ) + "||\n"
        s += "||" + "||".join([f"<center>{i}</center>" for i in ["**Requirements**",
                str(counts.units), str(counts.satisfied),
                str(counts.unsatisfied), str(counts.untested)]]) + "||\n"
        return s + "\n"

    def format_table(self, data):
        reqs = data["requirements"]
        s = "\n\n## Coverage\n"
        for r in reqs.values():
            s += f'\n  <div class="requirement"><span class="requirement-inline"><i class="utf-icon {self.icon_colors[r["status"]]}">{self.utf_icons[r["status"]]}</i>{r["requirement"].name}</span></div>'
            description = r["requirement"].description.replace("\\n","\n")
            if description:
                s += f'<div markdown="1" class="requirement-description hidden">{description}</div>'
            for test in r["tests"]:
                result = test["result"]
                cls = result.name.lower()
                s += f'<span class="result result-inline result-{cls}">{result.name}</span><span class="time time-inline">{strftimedelta(result.p_time)}</span>{test["test"].name}<br>'
            if not r["tests"]:
                s += f'<div class="no-tests"><span class="result-inline">\u270E</span>No tests</div>'
            s += "\n  "
        return s + "\n"

    def format(self, data):
        body = ""
        body += self.format_metadata(data)
        body += self.format_summary(data)
        body += self.format_statistics(data)
        body += self.format_table(data)
        return template.strip() % {"body": body, "script": script}

class Counts(object):
    def __init__(self, name, units, satisfied, unsatisfied, untested):
        self.name = name
        self.units = units
        self.satisfied = satisfied
        self.unsatisfied = unsatisfied
        self.untested = untested

    def __bool__(self):
        return self.units > 0

class Handler(HandlerBase):
    @classmethod
    def add_command(cls, commands):
        parser = commands.add_parser("requirements-coverage", help="requirements coverage report", epilog=epilog(),
            description="Generate requirements coverage report.",
            formatter_class=HelpFormatter)

        parser.add_argument("requirements", metavar="source", type=str,
                help="requirements source file")
        parser.add_argument("input", metavar="input", type=argtype.file("r", bufsize=1, encoding="utf-8"),
                nargs="?", help="input log, default: stdin", default="-")
        parser.add_argument("output", metavar="output", type=argtype.file("w", bufsize=1, encoding="utf-8"),
                nargs="?", help='output file, default: stdout', default="-")
        parser.add_argument("--show", metavar="status", type=str, nargs="+", help="verification status. Choices: 'satisfied', 'unsatisfied', 'untested'",
            choices=["satisfied", "unsatisfied", "untested"],
            default=["satisfied", "unsatisfied", "untested"])
        parser.add_argument("--input-link", metavar="attribute",
            help="attribute that is used as a link to the input log, default: job.url",
            type=str, default="job.url")
        parser.add_argument("--format", metavar="type", type=str,
            help="output format, default: md (Markdown)", choices=["md"], default="md")

        parser.set_defaults(func=cls())

    def get_attribute(self, result, name, default=None):
        tests = list(result["tests"].values())

        if not tests:
            return default

        test = tests[0]["test"]
        for attr in test.attributes:
            if attr.name == name:
                return attr.value

        return default

    def table(self, results):
        table = {
            "header": ["Requirement", "Tests"],
            "rows": [],
        }

        return table

    def metadata(self, results):
        return {
            "date": time.time(),
            "version": __version__,
        }

    def requirements(self, path):
        spec = importlib.util.spec_from_file_location("requirements", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _requirements = {}

        for name, value in vars(module).items():
            if not isinstance(value, Requirement):
                continue
            _requirements[value.name] = {"requirement": value, "tests": []}

        return _requirements

    def add_tests(self, requirements, results):
        for test in results["tests"].values():
            result = test["result"]
            if result.p_type < TestType.Test:
                continue
            for requirement in test["test"].requirements:
                if requirement.name in requirements:
                    requirements[requirement.name]["tests"].append(test)
        return requirements

    def counts(self, requirements):
        counts = Counts("requirements", *([0] * 4))

        for req in requirements.values():
            counts.units += 1
            tests = req["tests"]
            if not tests:
                counts.untested += 1
                req["status"] = "untested"
            else:
                satisfied = True
                for test in tests:
                    result = test["result"]
                    if result.name != "OK" and not result.name.startswith("X"):
                        satisfied = False
                if satisfied:
                    counts.satisfied += 1
                    req["status"] = "satisfied"
                else:
                    counts.unsatisfied += 1
                    req["status"] = "unsatisfied"
        return counts

    def data(self, source, results, input_link=None):
        d = dict()
        requirements = self.requirements(source)
        d["requirements"] = self.add_tests(requirements, results)
        d["metadata"] = self.metadata(results)
        d["counts"] = self.counts(d["requirements"])
        counts = d["counts"]
        return d

    def generate(self, formatter, results, args):
        output = args.output
        output.write(
            formatter.format(
                self.data(
                    args.requirements,
                    results,
                    input_link=args.input_link
                )
            )
        )
        output.write("\n")

    def handle(self, args):
        results = {}
        formatter = Formatter()
        ResultsLogPipeline(args.input, results).run()
        self.generate(formatter, results, args)
