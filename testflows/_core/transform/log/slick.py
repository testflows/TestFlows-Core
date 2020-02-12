# Copyright 2020 Vitaliy Zakaznikov (TestFlows Test Framework http://testflows.com)
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
from testflows._core.transform.log import message
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
        return color(icon, "white", attrs=["dim"])
    elif result == "Error":
        return color(icon, "yellow", attrs=["bold"])
    elif result == "Fail":
        return color(icon, "red", attrs=["bold"])
    # Null
    return color(icon, "cyan", attrs=["bold"])

def format_input(msg, last_test_id, keyword):
    flags = Flags(msg.p_flags)
    if flags & SKIP and settings.show_skipped is False:
        return
    out = f"{indent * (msg.p_id.count('/'))}"
    out += color("\u270b " + msg.message, "yellow", attrs=["bold"]) + cursor_up() + "\n"
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
    if msg.p_type == TestType.Module:
        return "Module"
    elif msg.p_type == TestType.Suite:
        if msg.p_subtype == TestSubType.Feature:
            return "Feature"
        else:
            return "Suite"
    else:
        if msg.p_subtype == TestSubType.Scenario:
            return "Scenario"
        elif msg.p_subtype == TestSubType.Background:
            return "Background"
        else:
            return "Test"

def format_test(msg, last_test_id, keyword):
    flags = Flags(msg.p_flags)
    if flags & SKIP and settings.show_skipped is False:
        return

    if msg.p_type < TestType.Test:
        return

    icon = '\u27A4 '

    keyword += format_type(msg)

    _keyword = color_keyword(keyword)
    _name = color_test_name(split(msg.name)[-1])
    _indent = indent * (msg.p_id.count('/') - 1)
    out = f"{_indent}{icon}{_keyword} {_name}\n"

    if last_test_id:
        last_test_id.pop()
    last_test_id.append(msg.p_id)

    return out

def format_result(msg, last_test_id, result):
    flags = Flags(msg.p_flags)
    if flags & SKIP and settings.show_skipped is False:
        return

    if msg.p_type < TestType.Test:
        return

    _result = color_result(result)
    _test = color_keyword(format_type(msg)) + color_test_name(f" {basename(msg.test)}")

    _indent = indent * (msg.p_id.count('/') - 1)
    out = f"{_indent}{_result}"

    if last_test_id[-1] == msg.p_id:
        out = cursor_up() + "\r" + out

    if msg.name in ("Fail", "Error", "Null"):
        out += f" {_test}"
        if msg.message:
            out += color_test_name(",")
            out += f" {color(format_multiline(msg.message, _indent).lstrip(), 'yellow', attrs=['bold'])}"
    elif msg.name.startswith("X"):
        out += f" {_test}"
        if msg.reason:
            out += color_test_name(",")
            out += f" {color(msg.reason, 'blue', attrs=['bold'])}"
    else:
        out += f" {_test}"
    return out + "\n"

formatters = {
    message.RawInput: (format_input, f""),
    message.RawTest: (format_test, f""),
    message.RawResultOK: (format_result, f"OK"),
    message.RawResultFail: (format_result, f"Fail"),
    message.RawResultError: (format_result, f"Error"),
    message.RawResultSkip: (format_result, f"Skip"),
    message.RawResultNull: (format_result, f"Null"),
    message.RawResultXOK: (format_result, f"XOK"),
    message.RawResultXFail: (format_result, f"XFail"),
    message.RawResultXError: (format_result, f"XError"),
    message.RawResultXNull: (format_result, f"XNull")
}

def transform():
    """Transform parsed log line into a clean format.
    """
    last_test_id = []
    line = None
    while True:
        if line is not None:
            formatter = formatters.get(type(line), None)
            if formatter:
                line = formatter[0](line, last_test_id, *formatter[1:])
            else:
                line = None
        line = yield line