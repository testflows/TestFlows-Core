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

from testflows._core.flags import Flags, SKIP
from testflows._core.cli.colors import color
from testflows._core.message import Message
from testflows._core.testtype import TestType

width = 70
count = 0


def color_result(result):
    if result.startswith("X"):
        return color(".", "blue", attrs=["bold"])
    elif result == "OK":
        return color(".", "green", attrs=["bold"])
    elif result == "Skip":
        return color("-", "white", attrs=["dim"])
    # Error, Fail, Null
    elif result == "Error":
        return color("E", "yellow", attrs=["bold"])
    elif result == "Fail":
        return color("F", "red", attrs=["bold"])
    elif result == "Null":
        return color("N", "magenta", attrs=["bold"])
    else:
        raise ValueError(f"unknown result {result}")


def format_prompt(msg):
    global count
    lines = (msg["message"] or "").splitlines()
    icon = "\u270d  "
    if msg["message"].startswith("Paused"):
        icon = "\u270b "
    out = ""
    if count > 0:
        out += "\n"
    out += color(icon + lines[0], "yellow", attrs=["bold"])
    if len(lines) > 1:
        out += "\n" + color("\n".join(lines[1:]), "white", attrs=["dim"])
    count = 0
    return out


def format_input(msg):
    global count
    out = color(msg["message"], "white") + "\n"
    count = 0
    return out


def format_result(msg):
    global count
    flags = Flags(msg["test_flags"])
    if flags & SKIP and settings.show_skipped is False:
        return

    if getattr(TestType, msg["test_type"]) < TestType.Iteration:
        return

    count += 1
    _result = f"{color_result(msg['result_type'])}"
    # wrap if we hit max width
    if count >= width:
        count = 0
        _result += "\n"

    return _result


formatters = {
    Message.INPUT.name: (format_input,),
    Message.PROMPT.name: (format_prompt,),
    Message.RESULT.name: (format_result,),
}


def transform(stop_event, show_input=True):
    """Transform parsed log line into a short format."""
    line = None
    while True:
        if line is not None:
            formatter = formatters.get(line["message_keyword"], None)
            if formatter:
                if formatter[0] is format_input and show_input is False:
                    line = None
                else:
                    line = formatter[0](line, *formatter[1:])
                    n = 0
            else:
                line = None

        if stop_event.is_set():
            if line is None:
                line = ""
            line += "\n"
        line = yield line
