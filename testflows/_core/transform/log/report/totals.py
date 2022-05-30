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
import testflows.settings as settings

from testflows._core.flags import Flags, SKIP, NESTED_RETRY
from testflows._core.testtype import TestType, TestSubType
from testflows._core.message import Message
from testflows._core.utils.timefuncs import strftimedelta
from testflows._core.cli.colors import color

def color_line(line):
    return color(line, "white", attrs=["dim"])

def color_result(result, text):
    if result.startswith("X"):
        return color(text, "blue", attrs=["bold"])
    elif result == "OK":
        return color(text, "green", attrs=["bold"])
    elif result == "Skip":
        return color(text, "white", attrs=["dim"])
    # Error, Fail, Null
    elif result == "Error":
        return color(text, "yellow", attrs=["bold"])
    elif result == "Fail":
         return color(text, "red", attrs=["bold"])
    elif result == "Null":
        return color(text, "magenta", attrs=["bold"])
    # Retried
    elif result == "Retried":
        return color(text, "cyan", attrs=["bold"])
    else:
        raise ValueError(f"unknown result {result}")

class Counts(object):
    def __init__(self, name, units, ok, fail, skip, error, null, xok, xfail, xerror, xnull, retried):
        self.name = name
        self.units = units
        self.ok = ok
        self.fail = fail
        self.skip = skip
        self.error = error
        self.null = null
        self.xok = xok
        self.xfail = xfail
        self.xerror = xerror
        self.xnull = xnull
        self.retried = retried

    def __bool__(self):
        return self.units > 0

    def __data__(self):
        data = {}
        counts = {}
        data["units"] = self.units
        data["name"] = self.name if self.units != 1 else self.name.rstrip('s')
        data["counts"] = counts
        if self.ok > 0:
            counts["OK"] = self.ok
        if self.fail > 0:
            counts["Fail"] = self.fail
        if self.skip > 0:
            counts["Skip"] = self.skip
        if self.error > 0:
            counts["Error"] = self.error
        if self.null > 0:
            counts["Null"] = self.null
        if self.xok > 0:
            counts["XOK"] = self.xok
        if self.xfail > 0:
            counts["XFail"] = self.xfail
        if self.xerror > 0:
            counts["XError"] = self.xerror
        if self.xnull > 0:
            counts["XNull"] = self.xnull
        if self.retried > 0:
            counts["Retried"] = self.retried
        return data

    def __str__(self):
        s = f"{self.units} {self.name if self.units != 1 else self.name.rstrip('s') if self.name != 'retries' else 'retry'}"
        s = color(s, "white", attrs=["bold"])
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
        if r:
            s += color(" (", "white", attrs=["bold"])
            s += color(", ", "white", attrs=["bold"]).join(r)
            s += color(")", "white", attrs=["bold"])
        s += "\n"
        return s

def format_test(msg, counts):
    flags = Flags(msg["test_flags"])

    if flags & SKIP and settings.show_skipped is False:
        return

    test_type = getattr(TestType, msg["test_type"])
    test_subtype = getattr(TestSubType, str(msg["test_subtype"]), 0)

    if test_subtype == TestSubType.Example:
        counts["example"].units += 1
    elif test_type == TestType.Module:
        if test_subtype == TestSubType.Book:
            counts["book"].units += 1
        else:
            counts["module"].units += 1
    elif test_type == TestType.Suite:
        if test_subtype == TestSubType.Feature:
            counts["feature"].units += 1
        if test_subtype == TestSubType.Chapter:
            counts["chapter"].units += 1
        else:
            counts["suite"].units += 1
    elif test_type == TestType.Outline:
        counts["outline"].units += 1
    elif test_type == TestType.Iteration:
        counts["iteration"].units += 1
    elif test_type == TestType.RetryIteration:
        counts["retry"].units += 1
    elif test_type == TestType.Step:
        if test_subtype == TestSubType.Paragraph:
            counts["paragraph"].units += 1
        else:
            counts["step"].units += 1
    else:
        if test_subtype == TestSubType.Scenario:
            counts["scenario"].units += 1
        elif test_subtype == TestSubType.Check:
            counts["check"].units += 1
        elif test_subtype == TestSubType.Critical:
            counts["critical"].units += 1
        elif test_subtype == TestSubType.Major:
            counts["major"].units += 1
        elif test_subtype == TestSubType.Minor:
            counts["minor"].units += 1
        elif test_subtype == TestSubType.Recipe:
            counts["recipe"].units += 1
        elif test_subtype == TestSubType.Document:
            counts["document"].units += 1
        elif test_subtype == TestSubType.Page:
            counts["page"].units += 1
        elif test_subtype == TestSubType.Section:
            counts["section"].units += 1
        else:
            counts["test"].units += 1

def format_result(msg, counts):
    flags = Flags(msg["test_flags"])
    cflags = Flags(msg["test_cflags"])

    if flags & SKIP and settings.show_skipped is False:
        return

    _name = msg["result_type"].lower()
    test_type = getattr(TestType, msg["test_type"])
    test_subtype = getattr(TestSubType, str(msg["test_subtype"]), 0)

    if cflags & NESTED_RETRY:
        if _name in ["fail", "error", "null"]:
            _name = "retried"

    if test_subtype == TestSubType.Example:
        setattr(counts["example"], _name, getattr(counts["example"], _name) + 1)
    elif test_type == TestType.Module:
        if test_subtype == TestSubType.Book:
            setattr(counts["book"], _name, getattr(counts["book"], _name) + 1)
        else:
            setattr(counts["module"], _name, getattr(counts["module"], _name) + 1)
    elif test_type == TestType.Suite:
        if test_subtype == TestSubType.Feature:
            setattr(counts["feature"], _name, getattr(counts["feature"], _name) + 1)
        if test_subtype == TestSubType.Chapter:
            setattr(counts["chapter"], _name, getattr(counts["chapter"], _name) + 1)
        else:
            setattr(counts["suite"], _name, getattr(counts["suite"], _name) + 1)
    elif test_type == TestType.Outline:
        setattr(counts["outline"], _name, getattr(counts["outline"], _name) + 1)
    elif test_type == TestType.Iteration:
        setattr(counts["iteration"], _name, getattr(counts["iteration"], _name) + 1)
    elif test_type == TestType.RetryIteration:
        setattr(counts["retry"], _name, getattr(counts["retry"], _name) + 1)
    elif test_type == TestType.Step:
        if test_subtype == TestSubType.Paragraph:
            setattr(counts["paragraph"], _name, getattr(counts["paragraph"], _name) + 1)
        else:
            setattr(counts["step"], _name, getattr(counts["step"], _name) + 1)
    else:
        if test_subtype == TestSubType.Scenario:
            setattr(counts["scenario"], _name, getattr(counts["scenario"], _name) + 1)
        elif test_subtype == TestSubType.Check:
            setattr(counts["check"], _name, getattr(counts["check"], _name) + 1)
        elif test_subtype == TestSubType.Critical:
            setattr(counts["critical"], _name, getattr(counts["critical"], _name) + 1)
        elif test_subtype == TestSubType.Major:
            setattr(counts["major"], _name, getattr(counts["major"], _name) + 1)
        elif test_subtype == TestSubType.Minor:
            setattr(counts["minor"], _name, getattr(counts["minor"], _name) + 1)
        elif test_subtype == TestSubType.Recipe:
            setattr(counts["recipe"], _name, getattr(counts["recipe"], _name) + 1)
        elif test_subtype == TestSubType.Document:
            setattr(counts["document"], _name, getattr(counts["document"], _name) + 1)
        elif test_subtype == TestSubType.Page:
            setattr(counts["page"], _name, getattr(counts["page"], _name) + 1)
        elif test_subtype == TestSubType.Section:
            setattr(counts["section"], _name, getattr(counts["section"], _name) + 1)
        else:
            setattr(counts["test"], _name, getattr(counts["test"], _name) + 1)

formatters = {
    Message.TEST.name: (format_test,),
    Message.RESULT.name: (format_result,)
}

def all_counts():
    return {
        "module": Counts("modules", *([0] * 11)),
        "book": Counts("books", *([0] * 11)),
        "suite": Counts("suites", *([0] * 11)),
        "feature": Counts("features", *([0] * 11)),
        "chapter": Counts("chapters", *([0] * 11)),
        "test": Counts("tests", *([0] * 11)),
        "outline": Counts("outlines", *([0] * 11)),
        "iteration": Counts("iterations", *([0] * 11)),
        "retry": Counts("retries", *([0] * 11)),
        "paragraph": Counts("paragraphs", *([0] * 11)),
        "step": Counts("steps", *([0] * 11)),
        "scenario": Counts("scenarios", *([0] * 11)),
        "recipe": Counts("recipes", *([0] * 11)),
        "check": Counts("checks", *([0] * 11)),
        "critical": Counts("critical", *([0] * 11)),
        "major": Counts("major", *([0] * 11)),
        "minor": Counts("minor", *([0] * 11)),
        "document": Counts("documents", *([0] * 11)),
        "page": Counts("pages", *([0] * 11)),
        "section": Counts("sections", *([0] * 11)),
        "example": Counts("examples", *([0] * 11))
    }

def transform(stop, divider="\n"):
    """Totals report.

    :param stop: stop event
    """
    counts = all_counts()
    line = None

    while True:
        if line is not None:
            msg = line
            formatter = formatters.get(line["message_keyword"], None)
            if formatter:
                formatter[0](line, *formatter[1:], counts=counts)
            line = None

        if stop.is_set():
            line = divider
            line_icon = "" #"\u27a4 "
            if counts["module"]:
                line += line_icon + str(counts["module"])
            if counts["book"]:
                line += line_icon + str(counts["book"])
            if counts["suite"]:
                line += line_icon + str(counts["suite"])
            if counts["feature"]:
                line += line_icon + str(counts["feature"])
            if counts["chapter"]:
                line += line_icon + str(counts["chapter"])
            if counts["test"]:
                line += line_icon + str(counts["test"])
            if counts["scenario"]:
                line += line_icon + str(counts["scenario"])
            if counts["check"]:
                line += line_icon + str(counts["check"])
            if counts["critical"]:
                line += line_icon + str(counts["critical"])
            if counts["major"]:
                line += line_icon + str(counts["major"])
            if counts["minor"]:
                line += line_icon + str(counts["minor"])
            if counts["recipe"]:
                line += line_icon + str(counts["recipe"])
            if counts["document"]:
                line += line_icon + str(counts["document"])
            if counts["page"]:
                line += line_icon + str(counts["page"])
            if counts["section"]:
                line += line_icon + str(counts["section"])
            if counts["example"]:
                line += line_icon + str(counts["example"])
            if counts["outline"]:
                line += line_icon + str(counts["outline"])
            if counts["iteration"]:
                line += line_icon + str(counts["iteration"])
            if counts["retry"]:
                line += line_icon + str(counts["retry"])
            if counts["paragraph"]:
                line += line_icon + str(counts["paragraph"])
            if counts["step"]:
                line += line_icon + str(counts["step"])
            line += color_line(f"\nTotal time {strftimedelta(msg['message_rtime'])}\n")

        line = yield line
