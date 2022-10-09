# Copyright 2021 Katteli Inc.
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
import testflows.settings as settings

from testflows._core.flags import Flags, SKIP, RETRY
from testflows._core.testtype import TestType
from testflows._core.message import Message
from testflows._core.name import split, parentname
from testflows._core.cli.colors import color
from testflows._core.transform.log.report.totals import Counts, color_result

indent = " " * 2

class UnstableCounts(Counts):
    def __str__(self):
        icon = "\u25D4"
        fail_rate = (self.fail + self.error + self.null)/self.units * 100
        if fail_rate in (0, 100):
            return ""
        fail_rate = color(f"{fail_rate:.2f}%", "cyan", attrs=["bold"])
        s = f"{color(icon, 'cyan', attrs=['bold'])} [ {fail_rate} ] {self.name} ("
        r = []
        if self.ok > 0:
            r.append(color_result("OK", f"{self.ok} ok"))
        if self.fail > 0:
            r.append(color_result("Fail", f"{self.fail} failed"))
        if self.skip > 0:
            r.append(color_result("Skip", f"{self.skip} skipped"))
        if self.error > 0:
            r.append(color_result("Error", f"{self.error} errored"))
        if self.null > 0:
            r.append(color_result("Null", f"{self.null} null"))
        if self.xok > 0:
            r.append(color_result("XOK", f"{self.xok} xok"))
        if self.xfail > 0:
            r.append(color_result("XFail", f"{self.xfail} xfail"))
        if self.xerror > 0:
            r.append(color_result("XError", f"{self.xerror} xerror"))
        if self.xnull > 0:
            r.append(color_result("XNull", f"{self.xnull} xnull"))
        if self.retried > 0:
            r.append(color_result("Retried", f"{self.retried} retried"))

        s += color(", ", "white", attrs=["bold"]).join(r)
        s += color(")\n", "white", attrs=["bold"])
        return s

def add_result(msg, results):
    flags = Flags(msg["test_flags"])
    cflags = Flags(msg["test_cflags"])

    if flags & SKIP and settings.show_skipped is False:
        return

    if (getattr(TestType, msg["test_type"]) == TestType.Iteration
            and not cflags & RETRY):
        result = msg["result_type"]
        parent_id, test_id = split(msg["test_id"])
        if results.get(parent_id) is None:
            results[parent_id] = []
        results[parent_id].append((msg, result))

processors = {
    Message.RESULT.name: (add_result,),
}

def generate(results, divider):
    """Generate report.
    """
    if not results:
        return

    unstable = ""

    for entry in results.values():
        name = parentname(entry[0][0]["test_name"])
        counts = UnstableCounts(name, *([0] * 11))
        for iteration in entry:
            msg, result = iteration
            counts.units += 1
            result_name = result.lower()
            setattr(counts, result_name, getattr(counts, result_name) + 1)
        _counts = str(counts)
        if _counts:
            _counts += "\n"
        unstable += _counts

    if unstable:
        unstable = color(f"{divider}Unstable\n\n", "white", attrs=["bold"]) + unstable.rstrip() + "\n"

    report = f"{unstable}"

    return report or None

def transform(stop, divider="\n"):
    """Generate unstable report.

    :param stop: stop event
    :param divider: report divider, default: `\n`
    """
    line = None
    results = {}
    while True:
        if line is not None:
            processor = processors.get(line["message_keyword"], None)
            if processor:
                processor[0](line, results, *processor[1:])
            line = None

        if stop.is_set():
            line = generate(results, divider)

        line = yield line
