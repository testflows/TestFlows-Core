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

from testflows._core.flags import Flags, SKIP, RETRY, LAST_RETRY
from testflows._core.testtype import TestType
from testflows._core.message import Message
from testflows._core.name import split, sep, parentname
from testflows._core.utils.timefuncs import strftimedelta
from testflows._core.cli.colors import color
from .brisk import transform as brisk_transform
from .nice import transform as nice_transform
from .plain import transform as plain_transform

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


def format_prompt(
    msg,
    dump_transform=None,
    buffer=None,
    skip_for_dump=None,
    skip_for_buffer=None,
    only_new=None,
):
    lines = (msg["message"] or "").splitlines()
    icon = "\u270d  "
    if msg["message"].startswith("Paused"):
        icon = "\u270b "
    out = color(icon + lines[0], "yellow", attrs=["bold"])
    if len(lines) > 1:
        out += "\n" + color("\n".join(lines[1:]), "white", attrs=["dim"])
    return out


def format_input(
    msg,
    dump_transform=None,
    buffer=None,
    skip_for_dump=None,
    skip_for_buffer=None,
    only_new=None,
):
    print("input", msg["message"])
    out = color(msg["message"], "white")
    return out


def format_multiline(text, indent):
    first, rest = (text.rstrip() + "\n").split("\n", 1)
    first = first.strip()
    if first:
        first += "\n"
    out = f"{first}{textwrap.dedent(rest.rstrip())}".rstrip()
    out = textwrap.indent(out, indent + "  ")
    return out


def collect_dump_messages(buffer, skip_for_dump, test_id):
    """Collect messages to dump for the failing test."""

    msgs = []
    if test_id not in buffer or test_id in skip_for_dump[0]:
        return msgs

    msgs += buffer[test_id]
    buffer[test_id] = []

    # get all child messages
    for name in buffer.keys():
        if name.startswith(test_id + sep):
            _msgs = buffer[name]
            if not _msgs:
                continue
            msgs += _msgs
            buffer[name] = []

    skip_test = test_id
    while skip_test and skip_test != sep:
        skip_for_dump[0].add(skip_test)
        skip_test = parentname(skip_test)

    msgs.sort(key=lambda x: x["message_time"])

    return msgs


def format_test(msg, dump_transform, buffer, skip_for_dump, skip_for_buffer, only_new):
    flags = Flags(msg["test_flags"])
    test_id = msg["test_id"]

    if flags & RETRY and not flags & LAST_RETRY:
        skip_for_buffer[0].add(test_id)

    return None


def format_result(
    msg, dump_transform, buffer, skip_for_dump, skip_for_buffer, only_new
):
    result = msg["result_type"]

    flags = Flags(msg["test_flags"])
    cflags = Flags(msg["test_cflags"])
    test_id = msg["test_id"]

    if flags & SKIP and settings.show_skipped is False:
        return

    if getattr(TestType, msg["test_type"]) < TestType.Iteration:
        return

    if cflags & RETRY and not flags & LAST_RETRY:
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
        _test_msgs = collect_dump_messages(buffer, skip_for_dump, test_id)
        if _test_msgs:
            g = dump_transform(show_input=True)
            g.send(None)
            out += "\n"
            for _test_msg in _test_msgs:
                g_out = g.send(_test_msg)
                if g_out is not None:
                    out += g_out
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

    skip_for_buffer[0].discard(test_id)
    return out


formatters = {
    Message.INPUT.name: (format_input,),
    Message.PROMPT.name: (format_prompt,),
    Message.TEST.name: (format_test,),
    Message.RESULT.name: (format_result,),
}


def transform(
    brisk=False, plain=False, nice=False, pnice=False, only_new=False, show_input=True
):
    """Transform parsed log line into a fails format.

    :param dump: dump messages of the failing test
    :param only_new: output only new fails
    """
    line = None
    buffer = {}
    skip_for_dump = [set()]
    skip_for_buffer = [set()]

    dump_transform = None
    if brisk:
        dump_transform = brisk_transform
    if plain:
        dump_transform = plain_transform
    if nice:
        dump_transform = nice_transform
    if pnice:
        dump_transform = functools.partial(nice_transform, add_test_name_prefix=True)

    while True:
        skip = False
        if line is not None:
            if dump_transform is not None:
                test_id = line["test_id"]

                if not test_id in buffer:
                    buffer[test_id] = []

                for _t in skip_for_buffer[0]:
                    if test_id.startswith(_t + sep):
                        skip = True
                        break
                if not skip:
                    buffer[test_id].append(line)

            formatter = formatters.get(line["message_keyword"], None)
            if skip:
                line = None
            elif formatter:
                if formatter[0] is format_input and show_input is False:
                    line = None
                else:
                    line = formatter[0](
                        line,
                        *formatter[1:],
                        dump_transform,
                        buffer,
                        skip_for_dump,
                        skip_for_buffer,
                        only_new,
                    )
            else:
                line = None
        line = yield line
