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
from testflows._core.testtype import TestType
from testflows._core.message import Message
from testflows._core.name import split
from testflows._core.utils.timefuncs import strftime, strftimedelta
from testflows._core.utils.timefuncs import localfromtimestamp
from testflows._core.cli.colors import color, cursor_up

indent = " " * 2

def color_other(other):
    return color(other, "white", attrs=["dim"])

def color_keyword(keyword):
    return color(split(keyword)[-1], "white", attrs=["dim"])

def color_secondary_keyword(keyword):
    return color(split(keyword)[-1], "white", attrs=["bold", "dim"])

def color_test_name(name):
    return color(name, "white", attrs=[])

def color_result(result, icon=None):
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

    if icon is None:
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

def format_input(msg, keyword):
    flags = Flags(msg["test_flags"])
    if flags & SKIP and settings.show_skipped is False:
        return
    out = f"{indent * (msg['test_id'].count('/'))}"
    out += color("\u270b " + msg["message"], "yellow", attrs=["bold"]) + cursor_up() + "\n\n"
    return out

def format_multiline(text, indent):
    first, rest = (text.rstrip() + "\n").split("\n", 1)
    first = first.strip()
    if first:
        first += "\n"
    out = f"{first}{textwrap.dedent(rest.rstrip())}".rstrip()
    out = textwrap.indent(out, indent + "  ")
    return out

def format_test(msg, keyword):
    flags = Flags(msg["test_flags"])
    if flags & SKIP and settings.show_skipped is False:
        return

    if getattr(TestType, msg["test_type"]) < TestType.Iteration:
        return

    icon = '\u27A4'
    time = f"{strftime(localfromtimestamp(msg['message_time'])):>20}"

    _name = color_test_name(msg["test_name"])
    out = f"{icon} {color_other(time)} {_name}\n"

    return out

def format_result(msg):
    result = msg["result_type"]

    flags = Flags(msg["test_flags"])
    if flags & SKIP and settings.show_skipped is False:
        return

    if getattr(TestType, msg["test_type"]) < TestType.Iteration:
        return

    _icon = color_result(result)
    _result = color_result(result, result)
    _test = color_test_name(f"{msg['result_test']}")

    out = f"{_icon} "+ color_other(f"{strftimedelta(msg['message_rtime']):<10}") + f"[ {result.center(6, ' ')} ]".ljust(10, ' ').replace(result, _result)

    if result in ("Fail", "Error", "Null"):
        out += f" {_test}"
        if msg["result_message"]:
            out += f"\n{indent}  {color(format_multiline(msg['result_message'], indent).lstrip(), 'yellow', attrs=['bold'])}"
    elif result.startswith("X"):
        out += f" {_test}"
        if msg['result_reason']:
            out += f"\n{indent}  {color(msg['result_reason'], 'blue', attrs=['bold'])}"
    else:
        out += f" {_test}"
    return out + "\n"

formatters = {
    Message.INPUT.name: (format_input, f""),
    Message.TEST.name: (format_test, f""),
    Message.RESULT.name: (format_result,)
}

def transform():
    """Transform parsed log line into a classic format.
    """
    line = None
    while True:
        if line is not None:
            formatter = formatters.get(line["message_keyword"], None)
            if formatter:
                line = formatter[0](line, *formatter[1:])
            else:
                line = None
        line = yield line
