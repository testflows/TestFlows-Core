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
        if not result.startswith("X"):
            return
    flags = Flags(msg["test_flags"])
    if flags & SKIP and settings.show_skipped is False:
        return
    if not result in ("OK", "Skip"):
        results[msg["test_id"]] = (msg, result)

processors = {
    Message.RESULT.name: (add_result,),
}

def generate(results, divider, only_new=False):
    """Generate report"""
    if not results:
        return

    xfails = ""
    fails = ""

    if not only_new:
        for entry in results:
            msg, result = results[entry]
            _color = color_result(result)
            if not result.startswith("X"):
                continue
            xfails += _color('\u2718') + f" [ { _color(result) } ] {msg['result_test']}"
            if msg["result_reason"]:
                xfails += color(f" \u1405 {msg['result_reason']}", "white", attrs=["dim"])
            xfails += "\n"

        if xfails:
            xfails = color("\nKnown\n\n", "white", attrs=["bold"]) + xfails

    for entry in results:
        msg, result = results[entry]
        _color = color_result(result)
        if result.startswith("X"):
            continue
        fails += _color("\u2718") + f" [ {_color(result)} ] {msg['result_test']}\n"
    if fails:
        fails = color(f"{divider}Failing\n\n", "white", attrs=["bold"]) + fails

    report = f"{xfails}{fails}"

    return report or None

def transform(stop, divider="\n", only_new=False):
    """Transform parsed log line into a short format.

    :param stop: stop event
    :param divider: report divider, default: `\n`
    :param only_new: output only new fails, default: `False`
    """
    line = None
    results = {}
    while True:
        if line is not None:
            processor = processors.get(line["message_keyword"], None)
            if processor:
                processor[0](line, results, *processor[1:])
            if stop.is_set():
                line = generate(results, divider, only_new)
            else:
                line = None
        line = yield line
