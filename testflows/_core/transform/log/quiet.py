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
import textwrap
import functools

import testflows.settings as settings

from testflows._core.flags import Flags, SKIP
from testflows._core.testtype import TestType, TestSubType
from testflows._core.message import Message
from testflows._core.utils.timefuncs import strftimedelta
from testflows._core.name import split, basename
from testflows._core.cli.colors import color

indent = " " * 2

def color_keyword(keyword):
    return color(split(keyword)[-1], "white", attrs=["bold"])

def color_secondary_keyword(keyword):
    return color(split(keyword)[-1], "white", attrs=["bold", "dim"])

def color_other(other):
    return color(other, "white", attrs=["dim"])

def color_result(result, attrs=None, retry=False):
    if attrs is None:
        attrs = ["bold"]
    if result.startswith("X"):
        return functools.partial(color, color="blue", attrs=attrs)
    elif result == "OK":
        return functools.partial(color, color="green", attrs=attrs)
    elif result == "Skip":
        return functools.partial(color, color="cyan", attrs=attrs)
    elif retry:
        return functools.partial(color, color="cyan", attrs=attrs)
    elif result == "Error":
        return functools.partial(color, color="yellow", attrs=attrs)
    elif result == "Fail":
        return functools.partial(color, color="red", attrs=attrs)
    elif result == "Null":
        return functools.partial(color, color="magenta", attrs=attrs)
    else:
        raise ValueError(f"unknown result {result}")

def format_prompt(msg, keyword):
    lines = (msg["message"] or "").splitlines()
    icon = "\u270d  "
    if msg["message"].startswith("Paused"):
        icon = "\u270b "
    out = color(icon + lines[0], "yellow", attrs=["bold"])
    if len(lines) > 1:
        out += "\n" + color("\n".join(lines[1:]), "white", attrs=["dim"])
    return out

def format_input(msg, keyword):
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

def get_type(msg):
    return getattr(TestType, msg["test_type"])

def get_subtype(msg):
    return getattr(TestSubType, str(msg["test_subtype"]), 0)

def format_result(msg, prefix):
    if int(msg["test_level"]) > 1:
        return

    result = msg["result_type"]

    if result in ("OK", "Skip") or result.startswith("X"):
        return

    _color = color_result(result)
    _result = _color(prefix + result)
    _test = color_other(basename(msg["result_test"]))
    _indent = f"{strftimedelta(msg['message_rtime']):>10}" + f"{'':3}{indent * (msg['test_id'].count('/') - 1)}"

    _result_message = msg["result_message"]
    if _result_message and settings.trim_results and int(msg["test_level"]) > 1:
        _result_message = _result_message.strip().split("\n",1)[0].strip()

    out = (f"{color_other(_indent)}{_result} "
        f"{_test}{color_other(', ' + msg['result_test'])}"
        f"{(color_other(', ') + _color(format_multiline(_result_message, ' ' * len(_indent)).strip())) if _result_message else ''}"
        f"{(color_other(', ') + _color(msg['result_reason'])) if msg['result_reason'] else ''}\n")

    return out

mark = "\u27e5"
result_mark = "\u27e5\u27e4"

formatters = {
    Message.INPUT.name: (format_input, f"{mark} "),
    Message.PROMPT.name: (format_prompt, f"{mark} "),
    Message.RESULT.name: (format_result, f"{result_mark} "),
}

def transform(show_input=True):
    """Transform parsed log line into a quiet format.
    Only output input, prompt messages as well as fails
    for top level test only.
    """
    line = None

    while True:
        if line is not None:
            msg = line
            formatter = formatters.get(line["message_keyword"], None)
            if formatter:
                if formatter[0] is format_input and show_input is False:
                    line = None
                else:
                    flags = Flags(line["test_flags"])
                    if flags & SKIP and settings.show_skipped is False:
                        line = None
                    else:
                        line = formatter[0](line, *formatter[1:])
            else:
                line = None

        line = yield line
