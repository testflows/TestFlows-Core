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
import textwrap

import testflows.settings as settings

from testflows._core.flags import Flags, SKIP
from testflows._core.testtype import TestType, TestSubType
from testflows._core.message import Message
from testflows._core.objects import ExamplesTable
from testflows._core.name import split, parentname, basename
from testflows._core.cli.colors import color, cursor_up

indent = " " * 2

def color_other(other):
    return color(other, "white", attrs=["dim"])

def color_keyword(keyword):
    return color(split(keyword)[-1], "white", attrs=["dim"])

def color_secondary_keyword(keyword):
    return color(split(keyword)[-1], "white", attrs=["bold", "dim"])

def color_test_name(name):
    return color(split(name)[-1], "white", attrs=[])

def color_result(result):
    def result_icon(result):
        r = result.lstrip("X")
        if r == "OK":
            return "\u2714"
        elif r == "Skip":
            return "\u2704"
        elif r == "Error":
            return "\u2718"
        elif r == "Fail":
            return "\u2718"
        else:
            return "\u2718"

    icon = result_icon(result)
    if result.startswith("X"):
        return color(icon, "blue", attrs=["bold"])
    elif result == "OK":
        return color(icon, "green", attrs=["bold"])
    elif result == "Skip":
        return color(icon, "cyan", attrs=["bold"])
    elif result == "Error":
        return color(icon, "yellow", attrs=["bold"])
    elif result == "Fail":
        return color(icon, "red", attrs=["bold"])
    # Null
    return color(icon, "magenta", attrs=["bold"])

def format_prompt(msg, last_test_id, keyword):
    lines = (msg["message"] or "").splitlines()
    icon = "\u270d  "
    if msg["message"].startswith("Paused"):
        icon = "\u270b "
    out = color(icon + lines[0], "yellow", attrs=["bold"])
    if len(lines) > 1:
        out += "\n" + color("\n".join(lines[1:]), "white", attrs=["dim"])
    return out

def format_input(msg, last_test_id, keyword):
    out = color(msg['message'], "white") + "\n"
    return out

def format_multiline(text, indent):
    first, rest = (text.rstrip() + "\n").split("\n", 1)
    first = first.strip()
    if first:
        first += "\n"
    out = f"{first}{textwrap.dedent(rest.rstrip())}".rstrip()
    out = textwrap.indent(out, indent + "  ")
    return out

def format_type(msg):
    test_type = getattr(TestType, msg["test_type"])
    test_subtype = getattr(TestSubType, str(msg["test_subtype"]), 0)

    if test_subtype == TestSubType.Example:
        return "Example"
    elif test_type == TestType.Module:
        if test_subtype == TestSubType.Book:
            return "Book"
        else:
            return "Module"
    elif test_type == TestType.Suite:
        if test_subtype == TestSubType.Feature:
            return "Feature"
        elif test_subtype == TestSubType.Chapter:
            return "Chapter"
        else:
            return "Suite"
    elif test_type == TestType.Outline:
        return "Outline"
    elif test_type == TestType.Iteration:
        return "Iteration"
    else:
        if test_subtype == TestSubType.Scenario:
            return "Scenario"
        elif test_subtype == TestSubType.Check:
            return "Check"
        elif test_subtype == TestSubType.Critical:
            return "Critical"
        elif test_subtype == TestSubType.Major:
            return "Major"
        elif test_subtype == TestSubType.Minor:
            return "Minor"
        elif test_subtype == TestSubType.Recipe:
            return "Recipe"
        elif test_subtype == TestSubType.Document:
            return "Document"
        elif test_subtype == TestSubType.Page:
            return "Page"
        elif test_subtype == TestSubType.Section:
            return "Section"
        else:
            return "Test"

def format_test(msg, last_test_id, keyword):
    flags = Flags(msg["test_flags"])
    if flags & SKIP and settings.show_skipped is False:
        return

    if getattr(TestType, msg["test_type"]) < TestType.Iteration:
        return

    icon = '\u27A4 '

    keyword += format_type(msg)

    _keyword = color_keyword(keyword)
    _name = color_test_name(split(msg["test_name"])[-1])
    _indent = indent * (msg["test_id"].count('/') - 1)
    out = f"{_indent}{icon}{_keyword} {_name}\n"

    last_test_id.append(msg["test_id"])

    return out

def format_result(msg, last_test_id):
    result = msg["result_type"]

    flags = Flags(msg["test_flags"])
    if flags & SKIP and settings.show_skipped is False:
        return

    if getattr(TestType, msg["test_type"]) < TestType.Iteration:
        return

    _result = color_result(result)
    _test = color_keyword(format_type(msg)) + color_test_name(f" {basename(msg['result_test'])}")

    _indent = indent * (msg["test_id"].count('/') - 1)
    out = f"{_indent}{_result}"

    if last_test_id and last_test_id[-1] == msg["test_id"]:
        out = cursor_up() + "\r" + out
    last_test_id = []

    _result_message = msg["result_message"]
    if _result_message and settings.trim_results and int(msg["test_level"]) > 1:
        _result_message = _result_message.strip().split("\n",1)[0].strip()

    if result in ("Fail", "Error", "Null"):
        out += f" {_test}"
        if _result_message:
            out += color_test_name(",")
            out += f" {color(format_multiline(_result_message, _indent).lstrip(), 'yellow', attrs=['bold'])}"
    elif result.startswith("X"):
        out += f" {_test}"
        if msg['result_reason']:
            out += color_test_name(",")
            out += f" {color(msg['result_reason'], 'blue', attrs=['bold'])}"
    else:
        out += f" {_test}"
    return out + "\n"

formatters = {
    Message.INPUT.name: (format_input, f""),
    Message.PROMPT.name: (format_prompt, f""),
    Message.TEST.name: (format_test, f""),
    Message.RESULT.name: (format_result,)
}

def transform(show_input=True):
    """Transform parsed log line into a clean format.
    """
    last_test_id = []
    line = None
    while True:
        if line is not None:
            formatter = formatters.get(line["message_keyword"], None)
            if formatter:
                if formatter[0] is format_input and show_input is False:
                    line = None
                else:
                    line = formatter[0](line, last_test_id, *formatter[1:])
            else:
                line = None
        line = yield line
