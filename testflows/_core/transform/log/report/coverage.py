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
import functools
import testflows.settings as settings

from testflows._core.flags import Flags, SKIP
from testflows._core.message import Message
from testflows._core.cli.colors import color
from testflows._core.document.srs import Parser, visit_parse_tree
from testflows._core.document.toc import Visitor as VisitorBase

def color_line(line):
    return color(line, "white", attrs=["dim"])

def color_counts(result):
    if result == "Satisfied":
        return functools.partial(color, color="green", attrs=["bold"])
    elif result == "Unsatisfied":
        return functools.partial(color, color="red", attrs=["bold"])
    # Untested
    return functools.partial(color, color="yellow", attrs=["bold"])

class Heading(object):
    def __init__(self, name, level, num):
        self.name = name
        self.level = level
        self.num = num

class Requirement(Heading):
    def __init__(self, name, version, uid, level, num):
        self.version = version
        self.uid = uid
        return super(Requirement, self).__init__(name, level, num)

class Visitor(VisitorBase):
    def __init__(self, *args, **kwargs):
        self.headings = []
        super(Visitor, self).__init__(*args, **kwargs)

    def visit_line(self, node, children):
        pass

    def visit_requirement(self, node, children):
        name = node.requirement_heading.requirement_name.value
        description = None
        uid = None
        version = None
        try:
            uid = f"\"{node.uid.word}\""
        except:
            pass
        try:
            version = f"\"{node.version.word}\""
        except:
            pass
        res = self.process_heading(node, children)
        if res:
            level, num = res
            self.headings.append(Requirement(name, version, uid, level, num))

    def visit_heading(self, node, children):
        res = self.process_heading(node, children)
        if res:
            level, num = res
            name = node.heading_name.value
            self.headings.append(Heading(name, level, num))

    def visit_document(self, node, children):
        return self.headings

class Counts(object):
    def __init__(self, name, units, ok, nok, untested):
        self.name = name
        self.units = units
        self.ok = ok
        self.nok = nok
        self.untested = untested

    def __bool__(self):
        return self.units > 0

    def __str__(self):
        s = f"{self.units} {self.name if self.units != 1 else self.name.rstrip('s')} ("
        s = color(s, "white", attrs=["bold"])
        r = []
        if self.ok > 0:
            r.append(color_counts("Satisfied")(f"{self.ok} satisfied {(self.ok / self.units) * 100:.1f}%"))
        if self.nok > 0:
            r.append(color_counts("Unsatisfied")(f"{self.nok} unsatisfied {(self.nok / self.units) * 100:.1f}%"))
        if self.untested > 0:
            r.append(color_counts("Untested")(f"{self.untested} untested {(self.untested / self.units) * 100:.1f}%"))
        s += color(", ", "white", attrs=["bold"]).join(r)
        s += color(")\n", "white", attrs=["bold"])
        return s

class Coverage:
    def __init__(self, specification):
        self.specification = specification
        self.requirements = self.parse_requirements(self.specification)
        self.counts = Counts("requirements", units=len(self.requirements), ok=0, nok=0, untested=0)

    @staticmethod
    def parse_requirements(specification):
        requirements = {}
        parser = Parser()
        tree = parser.parse(specification["specification_content"])

        for heading in visit_parse_tree(tree, Visitor()):
            if isinstance(heading, Requirement):
                requirements[heading.name] = []

        return requirements

    def calculate(self):
        """Calculate coverage.
        """
        for requirement, tests in self.requirements.items():
            if not tests:
                self.counts.untested += 1
            else:
                if sum([0 if test["result"] is not None and test["result"]["result_type"] == "OK" else 1 for test in tests]) == 0:
                    self.counts.ok += 1
                else:
                    self.counts.nok += 1
        return self

    def __str__(self):
        s = color(self.specification["specification_name"], "white", attrs=["bold", "dim"])
        s += f"\n  {self.counts}"
        return s

    def __contains__(self, requirement_name):
        return requirement_name in self.requirements

def format_test(msg, coverages, results):
    flags = Flags(msg["test_flags"])
    if flags & SKIP and settings.show_skipped is False:
        return
    results[msg["test_id"]] = {"test": msg, "requirements": [], "result": None}

def format_specification(msg, coverages, results):
    flags =  Flags(msg["test_flags"])
    if flags  & SKIP and settings.show_skipped is False:
        return
    coverages.append(Coverage(msg))

def format_requirement(msg, coverages, results):
    flags =  Flags(msg["test_flags"])
    if flags  & SKIP and settings.show_skipped is False:
        return
    test_id = msg["test_id"]
    requirement_name = msg["requirement_name"]

    if results.get(test_id) is None:
        return

    results[test_id]["requirements"].append(msg)

    for coverage in coverages:
        if requirement_name in coverage.requirements:
            coverage.requirements[requirement_name].append(results[test_id])

def format_result(msg, coverages, results):
    flags = Flags(msg["test_flags"])
    if flags & SKIP and settings.show_skipped is False:
        return
    test_id = msg["test_id"]

    if results.get(test_id) is None:
        return

    if not results[test_id]["requirements"]:
        del results[test_id]
    else:
        results[test_id]["result"] = msg

formatters = {
    Message.TEST.name: (format_test,),
    Message.SPECIFICATION.name: (format_specification,),
    Message.REQUIREMENT.name: (format_requirement,),
    Message.RESULT.name: (format_result,)
}

def generate(coverages, divider):
    """Generate report.
    """
    report = ""
    total_counts = Counts("requirements", units=0, ok=0, nok=0, untested=0)

    if coverages:
        report += color(f"{divider}Coverage\n", "white", attrs=["bold"])

    for coverage in coverages:
        report += f"\n{coverage.calculate()}"
        total_counts.units += coverage.counts.units
        total_counts.ok += coverage.counts.ok
        total_counts.nok += coverage.counts.nok
        total_counts.untested += coverage.counts.untested

    if len(coverages) > 1:
        s = color("Total", "white", attrs=["bold", "dim"])
        s += f"\n  {total_counts}"
        report += f"\n{s}"

    return report or None

def transform(stop, divider="\n"):
    """Totals report.

    :param stop: stop event
    """
    line = None
    coverages = []
    results = {}

    while True:
        if line is not None:
            formatter = formatters.get(line["message_keyword"], None)
            if formatter:
                formatter[0](line, *formatter[1:], coverages, results)
            line = None

        if stop.is_set():
            line = generate(coverages, divider)

        line = yield line
