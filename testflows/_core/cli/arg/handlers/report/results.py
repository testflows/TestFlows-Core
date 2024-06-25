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
import json
import time
import math
import base64

from json import JSONEncoder

import testflows.settings as settings
import testflows._core.cli.arg.type as argtype

from testflows._core import __version__
from testflows._core.flags import Flags, SKIP, RETRY
from testflows._core.testtype import TestType
from testflows._core.cli.arg.common import epilog
from testflows._core.cli.arg.common import HelpFormatter
from testflows._core.cli.arg.handlers.handler import Handler as HandlerBase
from testflows._core.cli.arg.handlers.report.copyright import copyright
from testflows._core.transform.log.pipeline import ResultsLogPipeline
from testflows._core.utils.timefuncs import localfromtimestamp, strftimedelta
from testflows._core.utils.string import title as make_title

FailResults = ["Fail", "Error", "Null"]
XoutResults = ["XOK", "XFail", "XError", "XNull"]

logo = '<img class="logo" src="data:image/png;base64,%(data)s" alt="logo"/>'
testflows = '<span class="testflows-logo"></span> [<span class="logo-test">Test</span><span class="logo-flows">Flows</span>]'
testflows_em = testflows.replace("[", "").replace("]", "")
template = f"""
<section class="clearfix">%(logo)s%(confidential)s%(copyright)s</section>

---
# %(name)s Test Run Report
%(body)s

---
Generated by {testflows} Open-Source Test Framework v%(generated_by_version)s

[<span class="logo-test">Test</span><span class="logo-flows">Flows</span>]: https://testflows.com
"""

results_order = [
    "Skip",
    "OK",
    "Fail",
    "Error",
    "Null",
    "XOK",
    "XFail",
    "XError",
    "XNull",
    "Retried",
]


class JSONFormatter:
    """JSON formatter."""

    class Encoder(JSONEncoder):
        def default(self, o):
            return vars(o)

    def format(self, data):
        return json.dumps(data, indent=2, cls=JSONFormatter.Encoder)


class MarkdownFormatter:
    """Markdown formatter."""

    def format_logo(self, data):
        if not data["company"].get("logo"):
            return ""
        data = base64.b64encode(data["company"]["logo"]).decode("utf-8")
        return "\n<p>" + logo % {"data": data} + "</p>\n"

    def format_confidential(self, data):
        if not data["company"].get("confidential"):
            return ""
        return f'\n<p class="confidential">Document status - Confidential</p>\n'

    def format_copyright(self, data):
        if not data["company"].get("name"):
            return ""
        return (
            f'\n<p class="copyright">\n'
            f'{copyright(data["company"]["name"])}\n'
            "</p>\n"
        )

    def format_artifacts(self, data):
        if not data["artifacts"]:
            return ""
        s = "\n## Artifacts\n"
        link = data["artifacts"]["link"]
        name = link.lstrip("./")
        s += f"Test artifacts can be found at "
        if link.startswith("http"):
            s += f"{link}\n"
        else:
            s += f"[{name}]({link})\n"
        return s

    def format_metadata(self, data):
        metadata = data["metadata"]

        duration = strftimedelta(metadata["duration"]) if metadata["duration"] else ""
        date = metadata["date"]
        version = metadata["version"]

        s = (
            "\n\n"
            f"||**Date**||{localfromtimestamp(date):%b %d, %Y %-H:%M}||\n"
            f"||**Duration**||{duration}||\n"
            f"||**Framework**||"
            f"{testflows} {version}||\n"
            "\n"
        )
        return s

    def format_summary(self, data):
        counts = data["counts"]

        def total(attribute, skip_keys=["step", "iteration", "retry"]):
            count = 0
            for key in counts.keys():
                if key in skip_keys:
                    continue
                count += getattr(counts[key], attribute)
            return count

        units = total("units")
        passed = total("ok")
        xout = total("xok") + total("xfail") + total("xerror") + total("xnull")
        failed = total("fail")
        nulled = total("null")
        errored = total("error")
        skipped = total("skip")
        retried = total("retried")

        def template(value, units, title, color):
            p_value = value / float(units) * 100
            if p_value > 1:
                value = f"{p_value:.1f}".rstrip("0").rstrip(".") + "%"
            else:
                value = f"<1%"
            return (
                f'<div class="c100 p{math.floor(p_value):.0f} {color}">'
                f"<span>{value}</span>"
                f'<span class="title">{title}</span>'
                '<div class="slice">'
                '<div class="bar"></div>'
                '<div class="fill"></div>'
                "</div>"
                "</div>\n"
            )

        s = "\n## Summary\n"

        if units <= 0:
            s += "No tests"
        else:
            s += '<div class="chart">'
            if settings.show_skipped:
                if skipped > 0:
                    s += template(skipped, units, "Skip", "gray")
            if passed > 0:
                s += template(passed, units, "OK", "green")
            if xout > 0:
                s += template(xout, units, "Known", "")
            if failed > 0:
                s += template(failed, units, "Fail", "red")
            if errored > 0:
                s += template(errored, units, "Error", "orange")
            if nulled > 0:
                s += template(nulled, units, "Null", "purple")
            if retried > 0:
                s += template(retried, units, "Retried", "cyan")
            s += "</div>"
        return s

    def format_statistics(self, data):
        s = "\n\n## Statistics\n"
        counts = data["counts"]

        statistics = {"types": {}}

        if counts["module"]:
            statistics["types"]["module"] = counts["module"].__data__()
        if counts["suite"]:
            statistics["types"]["suite"] = counts["suite"].__data__()
        if counts["test"]:
            statistics["types"]["test"] = counts["test"].__data__()
        if counts["feature"]:
            statistics["types"]["feature"] = counts["feature"].__data__()
        if counts["scenario"]:
            statistics["types"]["scenario"] = counts["scenario"].__data__()
        if counts["recipe"]:
            statistics["types"]["recipe"] = counts["recipe"].__data__()
        if counts["check"]:
            statistics["types"]["check"] = counts["check"].__data__()
        if counts["critical"]:
            statistics["types"]["critical"] = counts["critical"].__data__()
        if counts["major"]:
            statistics["types"]["major"] = counts["major"].__data__()
        if counts["minor"]:
            statistics["types"]["minor"] = counts["minor"].__data__()
        if counts["example"]:
            statistics["types"]["example"] = counts["example"].__data__()
        if counts["iteration"]:
            statistics["types"]["iteration"] = counts["iteration"].__data__()
        if counts["step"]:
            statistics["types"]["step"] = counts["step"].__data__()
        fields = set()
        for k in statistics["types"].values():
            fields = fields.union(set(k["counts"].keys()))
        statistics["result_fields"] = []

        for r in results_order:
            if r in fields:
                statistics["result_fields"].append(r)

        fields = ["<span></span>", "Units"] + [
            f'<span class="result result-{f.lower()}">{f}</span>'
            for f in statistics["result_fields"]
        ]
        s += " | ".join(fields) + "\n"
        s += " | ".join(["---"] * len(fields)) + "\n"
        for t in statistics["types"]:
            type_data = statistics["types"][t]
            c = [f"{t.capitalize()}s", f'<center>{str(type_data["units"])}</center>']
            for r in statistics["result_fields"]:
                if type_data["counts"].get(r):
                    c.append(f'<center>{str(type_data["counts"][r])}</center>')
                else:
                    c.append("")
            s += " | ".join(c) + "\n"
        return s + "\n"

    def format_attributes_and_tags(self, data):
        s = ""

        if data["attributes"]:
            s += "\n\n### Attributes\n"
            for attr in data["attributes"]:
                s += (
                    "||"
                    + "||".join(
                        [f"**{attr['attribute_name']}**", f"{attr['attribute_value']}"]
                    )
                    + "||\n"
                )
            s += "\n"

        if data["tags"]:
            s += "\n\n### Tags\n"
            for i, tag in enumerate(data["tags"]):
                if i > 0 and i % 3 == 0:
                    s += "||\n"
                s += f'||<strong class="tag tag-{i % 5}">{tag["tag_value"]}</strong>'
            s += "||\n"
        return s

    def format_fails(self, data):
        s = "\n\n## Fails\n"
        s += '<table class="stripped danger">\n'
        s += '<thead><tr><th><span style="display: block; min-width: 20vw;">Test Name</span></th><th><span style="display: block; min-width: 90px;">Result</span></th><th>Message</th></tr></thead>\n'
        s += "<tbody>\n"
        has_fails = False
        for test in data["tests"]:
            result = test["result"]
            flags = Flags(result["test_flags"])
            cflags = Flags(result["test_cflags"])
            if flags & SKIP and settings.show_skipped is False:
                continue
            if result["result_type"] in FailResults:
                cls = result["result_type"].lower()
                s += (
                    "<tr>"
                    + f'<td>{result["result_test"]}</td>'
                    + f'<td><span class="result result-{cls}">{result["result_type"]}</span>  '
                    + strftimedelta(result["message_rtime"])
                    + "</td>"
                    + '<td><div style="max-width: 30vw; overflow-x: auto;"><pre>'
                    + str(result["result_message"]).replace("|", r"\|")
                    + "</pre></div></td>"
                ) + "</tr>\n"
                has_fails = True
        s += "<tbody>\n"
        s += "</table>\n"
        if not has_fails:
            return ""
        return s

    def format_xfails(self, data):
        s = "\n\n## Known Fails\n"
        s += '<table class="stripped primary">\n'
        s += '<thead><tr><th><span style="display: block; min-width: 20vw;">Test Name</span></th><th><span style="display: block; min-width: 90px;">Result</span></th><th>Message</th></tr></thead>\n'
        s += "<tbody>\n"
        has_xfails = False
        for test in data["tests"]:
            result = test["result"]
            flags = Flags(result["test_flags"])
            if flags & SKIP and settings.show_skipped is False:
                continue
            if result["result_type"] in XoutResults:
                cls = result["result_type"].lower()
                s += (
                    "<tr>"
                    + f'<td>{result["result_test"]}</td>'
                    + f'<td><span class="result result-{cls}">{result["result_type"]}</span> '
                    + strftimedelta(result["message_rtime"])
                    + "<br>"
                    + str(result["result_reason"]).replace("|", r"\|")
                    + "</td>"
                    + '<td><div style="max-width: 30vw; overflow-x: auto;"><pre>'
                    + str(result["result_message"]).replace("|", r"\|")
                    + "</pre></div></td>"
                ) + "</tr>\n"
                has_xfails = True
        s += "<tbody>\n"
        s += "</table>\n"
        if not has_xfails:
            return ""
        return s

    def format_results(self, data):
        s = "\n## Results\n"
        s += (
            'Test Name | Result | <span style="display: block; min-width: 100px;">Duration</span>\n'
            "--- | --- | --- \n"
        )
        for test in data["tests"]:
            result = test["result"]
            flags = Flags(result["test_flags"])
            cflags = Flags(result["test_cflags"])
            if flags & SKIP and settings.show_skipped is False:
                continue
            cls = result["result_type"].lower()
            s += (
                " | ".join(
                    [
                        result["result_test"],
                        f'<span class="result result-{cls}">{result["result_type"]}</span>',
                        strftimedelta(result["message_rtime"]),
                    ]
                )
                + "\n"
            )
        return s

    def format(self, data):
        body = ""
        body += self.format_metadata(data)
        body += self.format_artifacts(data)
        body += self.format_attributes_and_tags(data)
        body += self.format_summary(data)
        body += self.format_statistics(data)
        body += self.format_fails(data)
        body += self.format_xfails(data)
        body += self.format_results(data)
        return template.strip() % {
            "logo": self.format_logo(data),
            "confidential": self.format_confidential(data),
            "copyright": self.format_copyright(data),
            "body": body,
            "name": data["name"],
            "generated_by_version": data["metadata"]["generated"]["version"],
        }


class Handler(HandlerBase):
    @classmethod
    def add_command(cls, commands):
        parser = commands.add_parser(
            "results",
            help="results report",
            epilog=epilog(),
            description="Generate results report.",
            formatter_class=HelpFormatter,
        )

        parser.add_argument(
            "input",
            metavar="input",
            type=argtype.logfile("r", bufsize=1, encoding="utf-8"),
            nargs="?",
            help="input log, default: stdin",
            default="-",
        )
        parser.add_argument(
            "output",
            metavar="output",
            type=argtype.file("w", bufsize=1, encoding="utf-8"),
            nargs="?",
            help="output file, default: stdout",
            default="-",
        )
        parser.add_argument(
            "-a", "--artifacts", metavar="link", type=str, help="link to the artifacts"
        )
        parser.add_argument(
            "--format",
            metavar="type",
            type=str,
            help="output format choices: 'md', 'json', default: md (Markdown)",
            choices=["md", "json"],
            default="md",
        )
        parser.add_argument(
            "--copyright", metavar="name", help="add copyright notice", type=str
        )
        parser.add_argument(
            "--confidential", help="mark as confidential", action="store_true"
        )
        parser.add_argument(
            "--logo",
            metavar="path",
            type=argtype.file("rb"),
            help="use logo image (.png)",
        )
        parser.add_argument("--title", metavar="name", help="custom title", type=str)

        parser.set_defaults(func=cls())

    def artifacts(self, link):
        if not link:
            return {}
        else:
            return {"name": link.lstrip("./"), "link": link}

    def attributes(self, results):
        if not results["tests"]:
            return []
        test = next(iter(results["tests"].values()), None)["test"]

        if test["attributes"]:
            return test["attributes"]
        return []

    def tags(self, results):
        if not results["tests"]:
            return []
        test = next(iter(results["tests"].values()), None)["test"]

        if test["tags"]:
            return test["tags"]
        return []

    def name(self, results):
        name = ""
        if results["tests"]:
            name = list(results["tests"].values())[0]["test"]["test_name"].lstrip("/")
        if name:
            name = make_title(name)
        return name

    def company(self, args):
        d = {}
        if args.copyright:
            d["name"] = args.copyright
        if args.confidential:
            d["confidential"] = True
        if args.logo:
            d["logo"] = args.logo.read()
        return d

    def metadata(self, results):
        duration = 0
        if results["tests"]:
            result = list(results["tests"].values())[0]["result"]
            duration = result["message_rtime"]
        return {
            "duration": duration,
            "date": results["started"],
            "version": results["version"],
            "generated": {
                "date": time.time(),
                "version": __version__,
            },
        }

    def counts(self, results):
        return results["counts"]

    def tests(self, results):
        tests = []
        for test in results["tests"].values():
            result = test["result"]
            if getattr(TestType, result["test_type"]) < TestType.Test:
                continue
            if result.get("test_parent_type"):
                if getattr(TestType, result["test_parent_type"]) < TestType.Suite:
                    continue
            if Flags(result["test_cflags"]) & RETRY:
                continue
            tests.append(test)
        return tests

    def data(self, results, args):
        d = dict()
        d["name"] = args.title or self.name(results)
        d["company"] = self.company(args)
        d["metadata"] = self.metadata(results)
        d["counts"] = self.counts(results)
        d["attributes"] = self.attributes(results)
        d["tags"] = self.tags(results)
        d["artifacts"] = self.artifacts(args.artifacts)
        d["tests"] = self.tests(results)
        return d

    def generate(self, formatter, results, args):
        output = args.output
        output.write(formatter.format(self.data(results, args)))
        output.write("\n")

    def handle(self, args):
        results = {}
        ResultsLogPipeline(args.input, results).run()
        formatter = MarkdownFormatter()
        if args.format == "json":
            formatter = JSONFormatter()
        self.generate(formatter, results, args)
