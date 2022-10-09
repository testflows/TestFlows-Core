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
import functools
import testflows.settings as settings

from testflows._core.flags import Flags, SKIP
from testflows._core.testtype import TestType
from testflows._core.message import Message
from testflows._core.name import split
from testflows._core.cli.colors import color
from testflows._core.utils.timefuncs import strftimedelta

indent = " " * 2

def color_result(result, attrs=None):
    if attrs is None:
        attrs = ["bold"]
    if result.startswith("X"):
        return functools.partial(color, color="blue", attrs=attrs)
    elif result == "OK":
        return functools.partial(color, color="green", attrs=attrs)
    elif result == "Skip":
        return functools.partial(color, color="cyan", attrs=attrs)
    # Error, Fail, Null
    elif result == "Error":
        return functools.partial(color, color="yellow", attrs=attrs)
    elif result == "Fail":
        return functools.partial(color, color="red", attrs=attrs)
    elif result == "Null":
        return functools.partial(color, color="magenta", attrs=attrs)
    else:
        raise ValueError(f"unknown result {result}")

def add_result(msg, results):
    result = msg["result_type"]
    if getattr(TestType, msg["test_type"]) < TestType.Iteration:
        return
    if msg.get("test_parent_type"):
        if getattr(TestType, msg["test_parent_type"]) < TestType.Suite:
            return
    flags = Flags(msg["test_flags"])
    if flags & SKIP and settings.show_skipped is False:
        return
    if result in ("OK", "Skip"):
        results[msg["test_id"]] = (msg, result)

processors = {
    Message.RESULT.name: (add_result,),
}

def generate(results, divider):
    """Generate report"""
    if not results:
        return

    passing = ""

    for entry in results:
        msg, result = results[entry]
        _color = color_result(result)
        passing += _color("\u2714") + f" [ {_color(result)} ] {msg['result_test']}"
        if msg["result_reason"]:
            passing += color(f" \u1405 {msg['result_reason']}", "white", attrs=["dim"])
        passing += " " + color("(" + strftimedelta(msg['message_rtime']) + ")", "white", attrs=["dim"])
        passing += "\n"
    if passing:
        passing = color(f"{divider}Passing\n\n", "white", attrs=["bold"]) + passing

    report = f"{passing}"

    return report or None

def transform(stop, divider="\n"):
    """Transform parsed log line into a short format.
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
