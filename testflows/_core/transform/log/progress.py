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

from testflows._core.flags import Flags, SKIP
from testflows._core.cli.colors import color
from testflows._core.message import Message
from testflows._core.testtype import TestType
from .report.totals import Counts
from .short import format_result as format_failing_result

progress = [
    color("Executing", "white", attrs=["dim"]),
    color("Executed", "white", attrs=["dim"])
]

def clear_line():
    return "\r\033[K\r"

def short_test_name(msg, max=80, tail=20):
    test_name = msg["test_name"]
    if len(test_name) > max:
        test_name = test_name[:max-tail] + "..." + test_name[-tail:]
    return color(test_name, "white", attrs=["dim"])

def format_prompt(msg, *_):
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

def format_input(msg, *_):
    global count
    out = color(msg['message'], "white") + "\n"
    count = 0
    return out

def format_result(msg, counter, counts):
    flags = Flags(msg["test_flags"])
    result = msg["result_type"]

    if flags & SKIP and settings.show_skipped is False:
        return
    if getattr(TestType, msg["test_type"]) < TestType.Iteration:
        return

    counter[0] += 1
    _result = msg["result_type"].lower()

    setattr(counts, _result, getattr(counts, _result) + 1)
    out = f"{clear_line()}{progress[counter[0] % (len(progress) - 1)]} {str(counts).rstrip()} {short_test_name(msg)}"
    if result in ("Fail", "Error", "Null"):
        out += "\n" + format_failing_result(msg, use_full_testname=True, use_indent=" "*2)
    return out

def format_test(msg, counter, counts):
    flags = Flags(msg["test_flags"])

    if flags & SKIP and settings.show_skipped is False:
        return
    if getattr(TestType, msg["test_type"]) >= TestType.Iteration:
        counts.units += 1
    counter[0] += 1

    return f"{clear_line()}{progress[counter[0] % (len(progress)-1)]} {str(counts).rstrip()} {short_test_name(msg)}"

def format_stop(msg, counter, counts):
    return f"{clear_line()}{progress[-1]} {counts}".rstrip()

formatters = {
    Message.INPUT.name: (format_input,),
    Message.PROMPT.name: (format_prompt,),
    Message.RESULT.name: (format_result,),
    Message.TEST.name: (format_test,),
    Message.STOP.name: (format_stop,)
}

def transform(stop_event, show_input=True):
    """Transform parsed log line into a progress format.
    """
    line = None
    counter = [-1]
    counts = Counts("tests", *([0] * 11))

    while True:
        if line is not None:
            formatter = formatters.get(line["message_keyword"], None)
            if formatter:
                if formatter[0] is format_input and show_input is False:
                    line = None
                else:
                    line = formatter[0](line, counter, counts, *formatter[1:])
                    n = 0
            else:
                line = None

        if stop_event.is_set():
            if line is None:
                line = ""
            line += "\n"
        line = yield line
