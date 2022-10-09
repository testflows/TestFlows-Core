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

from testflows._core.flags import Flags, SKIP, RETRY
from testflows._core.testtype import TestType
from testflows._core.message import Message
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
    elif result == "Error":
        return functools.partial(color, color="yellow", attrs=attrs)
    elif result == "Fail":
        return functools.partial(color, color="red", attrs=attrs)
    elif result == "Null":
        return functools.partial(color, color="magenta", attrs=attrs)
    else:
        raise ValueError(f"unknown result {result}")

def add_result(msg, results):
    flags = Flags(msg["test_flags"])
    cflags = Flags(msg["test_cflags"])
    result = msg["result_type"]

    if getattr(TestType, msg["test_type"]) < TestType.Iteration:
        if not result.startswith("X"):
            return
    if flags & SKIP and settings.show_skipped is False:
        return
    if cflags & RETRY:
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

    retries = ""
    xfails = ""
    fails = ""

    for entry in results:
        msg, result = results[entry]
        _color = color_result(result)

        out = _color("\u2718") + f" [ {_color(result)} ] {msg['result_test']}"
        if msg["result_reason"]:
            out += color(f" \u1405 {msg['result_reason']}", "white", attrs=["dim"])
        out += " " + color("(" + strftimedelta(msg['message_rtime']) + ")", "white", attrs=["dim"])
        out += "\n"

        if result.startswith("X"):
            if not only_new:
                xfails += out
        else:
            fails += out

    if retries:
        retries = color(f"{divider}Retries\n\n", "white", attrs=["bold"]) + retries

    if xfails:
        if not divider and retries:
            divider = "\n"
        xfails = color(f"{divider}Known\n\n", "white", attrs=["bold"]) + xfails

    if fails:
        if not divider and (xfails or retries):
            divider = "\n"
        fails = color(f"{divider}Failing\n\n", "white", attrs=["bold"]) + fails

    report = f"{retries}{xfails}{fails}"

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
            line = None

        if stop.is_set():
            line = generate(results, divider, only_new)

        line = yield line
