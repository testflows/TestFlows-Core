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
import functools

import testflows.settings as settings

from testflows._core.flags import Flags, SKIP
from testflows._core.testtype import TestType
from testflows._core.message import Message
from testflows._core.name import split, parentname
from testflows._core.utils.timefuncs import strftimedelta
from testflows._core.cli.colors import color
from .brisk import transform as brisk_transform
from .nice import transform as nice_transform

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


def get_type(msg):
    return getattr(TestType, msg["test_type"])


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
    out = color(msg["message"], "white") + "\n"
    return out


def format_multiline(text, indent):
    first, rest = (text.rstrip() + "\n").split("\n", 1)
    first = first.strip()
    if first:
        first += "\n"
    out = f"{first}{textwrap.dedent(rest.rstrip())}".rstrip()
    out = textwrap.indent(out, indent + "  ")
    return out


def format_result(msg, dump_transform, buffer, only_new):
    result = msg["result_type"]

    flags = Flags(msg["test_flags"])
    if flags & SKIP and settings.show_skipped is False:
        return

    if getattr(TestType, msg["test_type"]) < TestType.Iteration:
        return

    _icon = color_result(result)
    _result = color_result(result, result)
    _test = color_test_name(f"{msg['result_test']}")

    out = (
        f"{_icon} "
        + color_other(f"{strftimedelta(msg['message_rtime']):<10}")
        + f"[ {result.center(6, ' ')} ]".ljust(10, " ").replace(result, _result)
    )

    _result_message = msg["result_message"]
    if _result_message and settings.trim_results and int(msg["test_level"]) > 1:
        _result_message = _result_message.strip().split("\n", 1)[0].strip()

    if result in ("Fail", "Error", "Null"):
        out += f" {_test}"
        _test_msgs = buffer.pop(msg["test_id"], None)
        if _test_msgs:
            g = dump_transform(show_input=False)
            g.send(None)
            out += "\n"
            for _test_msg in _test_msgs:
                out += g.send(_test_msg)
            out = out.rstrip()
        if _result_message:
            out += f"\n{indent}  {color(format_multiline(_result_message, indent).lstrip(), 'yellow', attrs=['bold'])}"
        out += "\n"
    elif not only_new and result.startswith("X"):
        out += f" {_test}"
        if msg["result_reason"]:
            out += f"\n{indent}  {color(msg['result_reason'], 'blue', attrs=['bold'])}"
        out += "\n"
    else:
        out = None

    return out


formatters = {
    Message.INPUT.name: (format_input, f""),
    Message.PROMPT.name: (format_prompt, f""),
    Message.RESULT.name: (format_result,),
}


def transform(brisk=False, nice=False, pnice=False, only_new=False, show_input=True):
    """Transform parsed log line into a fails format.

    :param dump: dump messages of the failing test
    :param only_new: output only new fails
    """
    line = None
    buffer = {}

    dump_transform = None
    if brisk:
        dump_transform = brisk_transform
    if nice:
        dump_transform = nice_transform
    if pnice:
        dump_transform = functools.partial(nice_transform, add_test_name_prefix=True)

    while True:
        if line is not None:
            if dump_transform is not None:
                test_id = line["test_id"]
                parent_id = parentname(test_id)

                if get_type(line) > TestType.Step:
                    if not any(
                        [name for name in buffer.keys() if name.startswith(test_id)]
                    ):
                        if not test_id in buffer:
                            buffer[test_id] = []

                        buffer.pop(parent_id, None)

                    if test_id in buffer:
                        buffer[test_id].append(line)
                else:
                    for name in buffer.keys():
                        if test_id.startswith(name):
                            buffer[name].append(line)
                            break

            formatter = formatters.get(line["message_keyword"], None)
            if formatter:
                if formatter[0] is format_input and show_input is False:
                    line = None
                else:
                    line = formatter[0](
                        line, *formatter[1:], dump_transform, buffer, only_new
                    )
            else:
                line = None
        line = yield line
