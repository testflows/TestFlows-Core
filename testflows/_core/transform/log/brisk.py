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
import re
import textwrap
import functools

import testflows.settings as settings

from testflows._core.flags import Flags, SKIP, LAST_RETRY
from testflows._core.testtype import TestType, TestSubType
from testflows._core.message import Message
from testflows._core.objects import ExamplesTable
from testflows._core.utils.timefuncs import strftime, strftimedelta
from testflows._core.utils.timefuncs import localfromtimestamp
from testflows._core.name import split, basename, parentname, sep
from testflows._core.cli.colors import color, cursor_up

strip_nones = re.compile(r'( None)+$')
indent = " " * 2
#: map of tests by name
tests_by_name = {}
#: map of tests by parent
tests_by_parent = {}
#: map of parent of the test type by name
test_type_parent_by_name = {}
#: last message
last_message = [None]

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

def format_test_description(msg, indent):
    test_id = msg["test_id"]
    if test_type_parent_by_name[test_id] != test_id:
        return ''
    desc = format_multiline(msg["test_description"], indent)
    desc = color(desc, "white", attrs=["dim"])
    return desc + "\n"

def format_requirements(msg, indent):
    test_id = msg["test_id"]
    if test_type_parent_by_name[test_id] != test_id:
        return ''
    out = [f"{indent}{' ' * 2}{color_secondary_keyword('Requirements')}"]
    for req in msg.requirements:
        out.append(color(f"{indent}{' ' * 4}{req.name}", "white", attrs=["dim"]))
        out.append(color(f"{indent}{' ' * 6}version {req.version}", "white", attrs=["dim"]))
    return "\n".join(out) + "\n"

def format_attribute(msg):
    test_id = msg["test_id"]
    if test_type_parent_by_name[test_id] != test_id:
        return ''
    out = []
    _indent = f"{' ':>23}" + f"{'':3}{indent * (msg['test_id'].count('/') - 1)}"

    if last_message[0] and not last_message[0]["message_keyword"] == Message.ATTRIBUTE.name:
        out = [f"{_indent}{' ' * 2}{color_secondary_keyword('Attributes')}"]

    out.append(color(f"{_indent}{' ' * 4}{msg['attribute_name']}", "white", attrs=["dim"]))
    out.append(color(f"{textwrap.indent(str(msg['attribute_value']), prefix=(_indent + ' ' * 6))}", "white", attrs=["dim"]))
    return "\n".join(out) + "\n"

def format_specification(msg):
    test_id = msg["test_id"]
    if test_type_parent_by_name[test_id] != test_id:
        return ''
    out = []
    _indent = f"{' ':>23}" + f"{'':3}{indent * (msg['test_id'].count('/') - 1)}"

    if last_message[0] and not last_message[0]["message_keyword"] == Message.SPECIFICATION.name:
        out = [f"{_indent}{' ' * 2}{color_secondary_keyword('Specifications')}"]

    out.append(color(f"{_indent}{' ' * 4}{msg['specification_name']}", "white", attrs=["dim"]))
    if msg["specification_version"]:
        out.append(color(f"{_indent}{' ' * 6}version {msg['specification_version']}", "white", attrs=["dim"]))
    return "\n".join(out) + "\n"

def format_requirement(msg):
    test_id = msg["test_id"]
    if test_type_parent_by_name[test_id] != test_id:
        return ''
    out = []
    _indent = f"{' ':>23}" + f"{'':3}{indent * (msg['test_id'].count('/') - 1)}"

    if last_message[0] and not last_message[0]["message_keyword"] == Message.REQUIREMENT.name:
        out = [f"{_indent}{' ' * 2}{color_secondary_keyword('Requirements')}"]

    out.append(color(f"{_indent}{' ' * 4}{msg['requirement_name']}", "white", attrs=["dim"]))
    out.append(color(f"{_indent}{' ' * 6}version {msg['requirement_version']}", "white", attrs=["dim"]))
    return "\n".join(out) + "\n"

def format_tag(msg):
    test_id = msg["test_id"]
    if test_type_parent_by_name[test_id] != test_id:
        return ''
    out = []
    _indent = f"{' ':>23}" + f"{'':3}{indent * (msg['test_id'].count('/') - 1)}"

    if last_message[0] and not last_message[0]["message_keyword"] == Message.TAG.name:
        out = [f"{_indent}{' ' * 2}{color_secondary_keyword('Tags')}"]

    out.append(color(f"{_indent}{' ' * 4}{msg['tag_value']}", "white", attrs=["dim"]))
    return "\n".join(out) + "\n"

def format_example(msg):
    test_id = msg["test_id"]
    if test_type_parent_by_name[test_id] != test_id:
        return ''
    out = []
    _indent = f"{' ':>23}" + f"{'':3}{indent * (msg['test_id'].count('/') - 1)}"

    row_format = msg["example_row_format"] or ExamplesTable.default_row_format(msg["example_columns"], msg["example_values"])
    if last_message[0] and not last_message[0]["message_keyword"] == Message.EXAMPLE.name:
        out = [f"{_indent}{' ' * 2}{color_secondary_keyword('Examples')}"]
        out.append(color(textwrap.indent(f"{ExamplesTable.__str_header__(tuple(msg['example_columns']), row_format)}", prefix=f"{_indent}{' ' * 4}"), "white", attrs=["dim"]))

    out.append(color(textwrap.indent(f"{ExamplesTable.__str_row__(tuple(msg['example_values']),row_format)}", prefix=f"{_indent}{' ' * 4}"), "white", attrs=["dim"]))
    return "\n".join(out) + "\n"

def format_argument(msg):
    test_id = msg["test_id"]
    if test_type_parent_by_name[test_id] != test_id:
        return ''
    out = []
    _indent = f"{' ':>23}" + f"{'':3}{indent * (msg['test_id'].count('/') - 1)}"

    if last_message[0] and not last_message[0]["message_keyword"] == Message.ARGUMENT.name:
        out = [f"{_indent}{' ' * 2}{color_secondary_keyword('Arguments')}"]

    out.append(color(f"{_indent}{' ' * 4}{msg['argument_name']}", "white", attrs=["dim"]))
    out.append(color(textwrap.indent(f"{msg['argument_value']}", prefix=f"{_indent}{' ' * 6}"), "white", attrs=["dim"]))
    return "\n".join(out) + "\n"

def and_keyword(msg, parent_id, keyword, subtype):
    """Handle processing of Given, When, Then, But, By and Finally
    keywords and convert them to And when necessary.
    """
    prev = tests_by_parent[parent_id][-2] if len(tests_by_parent.get(parent_id, [])) > 1 else None
    if prev and get_subtype(prev) == subtype and tests_by_parent.get(prev["test_id"]) is None:
        keyword = "And"
    parent = tests_by_name.get(parent_id)
    if parent and get_subtype(parent) == subtype and len(tests_by_parent.get(parent_id, [])) == 1:
        keyword = "And"
    return keyword

def get_type(msg):
    return getattr(TestType, msg["test_type"])

def get_subtype(msg):
    return getattr(TestSubType, str(msg["test_subtype"]), 0)

def format_test(msg, keyword):
    # add test to the tests map
    test_id = msg["test_id"]
    parent = parentname(test_id)
    if tests_by_parent.get(parent) is None:
        tests_by_parent[parent] = []
    tests_by_parent[parent].append(msg)
    tests_by_name[test_id] = msg

    flags = Flags(msg["test_flags"])
    test_type = get_type(msg)
    test_subtype = get_subtype(msg)

    if test_type >= TestType.Test:
        test_type_parent_by_name[test_id] = test_id
    else:
        current_test_id = test_id
        while True:
            head, tail = current_test_id.rsplit(sep, 1)
            if not head:
                test_type_parent_by_name[test_id] = test_id
                break
            elif get_type(tests_by_name[head]) >= TestType.Test:
                test_type_parent_by_name[test_id] = head
                break
            current_test_id = head

    if test_type_parent_by_name[test_id] != test_id:
        return ''

    if test_subtype == TestSubType.Example:
        keyword += "Example"
    elif test_type == TestType.Module:
        if test_subtype == TestSubType.Book:
            keyword += "Book"
        else:
            keyword += "Module"
    elif test_type == TestType.Suite:
        if test_subtype == TestSubType.Feature:
            keyword += "Feature"
        elif test_subtype == TestSubType.Chapter:
            keyword += "Chapter"
        else:
            keyword += "Suite"
    elif test_type == TestType.Iteration:
        keyword += "Iteration"
    elif test_type == TestType.RetryIteration:
        keyword += "Retry"
    elif test_type == TestType.Step:
        if test_subtype == TestSubType.And:
            keyword += "And"
        elif test_subtype == TestSubType.Given:
            keyword += and_keyword(msg, parent, "Given", TestSubType.Given)
        elif test_subtype == TestSubType.When:
            keyword += and_keyword(msg, parent, "When", TestSubType.When)
        elif test_subtype == TestSubType.Then:
            keyword += and_keyword(msg, parent, "Then", TestSubType.Then)
        elif test_subtype == TestSubType.By:
            keyword += and_keyword(msg, parent, "By", TestSubType.By)
        elif test_subtype == TestSubType.But:
            keyword += and_keyword(msg, parent, "But", TestSubType.But)
        elif test_subtype == TestSubType.Finally:
            keyword += and_keyword(msg, parent, "Finally", TestSubType.Finally)
        elif test_subtype == TestSubType.Cleanup:
            keyword += and_keyword(msg, parent, "Cleanup", TestSubType.Cleanup)
        elif test_subtype == TestSubType.Background:
            keyword += and_keyword(msg, parent, "Background", TestSubType.Background)
        elif test_subtype == TestSubType.Paragraph:
            keyword += and_keyword(msg, parent, "Paragraph", TestSubType.Paragraph)
        else:
            keyword += "Step"
    elif test_type == TestType.Outline:
        keyword += "Outline"
    else:
        if test_subtype == TestSubType.Scenario:
            keyword += "Scenario"
        elif test_subtype == TestSubType.Check:
            keyword += "Check"
        elif test_subtype == TestSubType.Critical:
            keyword += "Critical"
        elif test_subtype == TestSubType.Major:
            keyword += "Major"
        elif test_subtype == TestSubType.Minor:
            keyword += "Minor"
        elif test_subtype == TestSubType.Recipe:
            keyword += "Recipe"
        elif test_subtype == TestSubType.Document:
            keyword += "Document"
        elif test_subtype == TestSubType.Page:
            keyword += "Page"
        elif test_subtype == TestSubType.Section:
            keyword += "Section"
        else:
            keyword += "Test"

    started = strftime(localfromtimestamp(msg["message_time"]))
    _keyword = color_keyword(keyword)
    _name = color_other(split(msg["test_name"])[-1])
    _indent = f"{started:>20}" + f"{'':3}{indent * (msg['test_id'].count('/') - 1)}"
    out = f"{color_other(_indent)}{_keyword} {_name}{color_other(', flags:' + str(flags) if flags else '')}\n"
    # convert indent to just spaces
    _indent = (len(_indent) + 3) * " "
    if msg["test_description"]:
        out += format_test_description(msg, _indent)
    return out

def format_result(msg, prefix):
    test_id = msg["test_id"]
    if test_type_parent_by_name[test_id] != test_id:
        return ''
    result = msg["result_type"]
    _retry = get_type(msg) == TestType.RetryIteration and LAST_RETRY not in Flags(msg["test_flags"])
    _color = color_result(result, retry=_retry)
    _result = _color(prefix + result)
    _test = color_other(basename(msg["result_test"]))
    _indent = f"{strftimedelta(msg['message_rtime']):>20}" + f"{'':3}{indent * (msg['test_id'].count('/') - 1)}"

    _result_message = msg["result_message"]
    if _result_message and settings.trim_results and int(msg["test_level"]) > 1:
        _result_message = _result_message.strip().split("\n", 1)[0].strip()

    out = (f"{color_other(_indent)}{_result} "
        f"{_test}{color_other(', ' + msg['result_test'])}"
        f"{(color_other(', ') + _color(format_multiline(_result_message, ' ' * len(_indent)).strip())) if _result_message else ''}"
        f"{(color_other(', ') + _color(msg['result_reason'])) if msg['result_reason'] else ''}\n")

    return out

def format_message(msg, keyword, prefix="", predicate=None):
    out = msg["message"]
    if msg["message_stream"]:
        out = f"[{msg['message_stream']}] {msg['message']}"

    out = textwrap.indent(out, prefix=(indent * (test_type_parent_by_name[msg["test_id"]].count('/') - 1) + " " * 30 + prefix), predicate=predicate)
    out = out.lstrip(" ")
    if out.endswith("\n"):
        out = out[:-1]

    return color_other(f"{strftimedelta(msg['message_rtime']):>20}{'':3}{indent * (test_type_parent_by_name[msg['test_id']].count('/') - 1)}{keyword} {color_other(out)}\n")

def format_metric(msg, keyword):
    prefix = f"{strftimedelta(msg['message_rtime']):>20}" + f"{'':3}{indent * (test_type_parent_by_name[msg['test_id']].count('/') - 1)}"
    _indent = (len(prefix) + 3) * " "
    out = [color_other(f"{prefix}{keyword}") + color("Metric", "white", attrs=["dim", "bold"]) + color_other(f" {msg['metric_name']}")]
    out.append(color_other(format_multiline(f"{msg['metric_value']} {msg['metric_units']}", _indent + " " * 2)))
    return "\n".join(out) + "\n"

def format_value(msg, keyword):
    prefix = f"{strftimedelta(msg['message_rtime']):>20}" + f"{'':3}{indent * (test_type_parent_by_name[msg['test_id']].count('/') - 1)}"
    _indent = (len(prefix) + 3) * " "
    out = [color_other(f"{prefix}{keyword}") + color("Value", "white", attrs=["dim", "bold"]) + color_other(f" {msg['value_name']}")]
    out.append(color_other(format_multiline(f"{msg['value_value']}", _indent + " " * 2)))
    return "\n".join(out) + "\n"

def format_ticket(msg, keyword):
    prefix = f"{strftimedelta(msg['message_rtime']):>20}" + f"{'':3}{indent * (test_type_parent_by_name[msg['test_id']].count('/') - 1)}"
    _indent = (len(prefix) + 3) * " "
    out = [color_other(f"{prefix}{keyword}") + color("Ticket", "white", attrs=["dim", "bold"]) + color_other(f" {msg['ticket_name']}")]
    out.append(color_other(format_multiline(f"{msg['ticket_link']}", _indent + " " * 2)))
    return "\n".join(out) + "\n"

mark = "\u27e5"
result_mark = "\u27e5\u27e4"

formatters = {
    Message.INPUT.name: (format_input, f"{mark} "),
    Message.PROMPT.name: (format_prompt, f"{mark} "),
    Message.TEST.name: (format_test, f"{mark}  "),
    Message.ATTRIBUTE.name: (format_attribute, ),
    Message.ARGUMENT.name: (format_argument,),
    Message.SPECIFICATION.name: (format_specification,),
    Message.REQUIREMENT.name: (format_requirement,),
    Message.TAG.name: (format_tag,),
    Message.EXAMPLE.name: (format_example,),
    Message.VALUE.name: (format_value, f"{mark}    "),
    Message.METRIC.name: (format_metric, f"{mark}    "),
    Message.TICKET.name: (format_ticket, f"{mark}    "),
    Message.EXCEPTION.name: (format_message, f"{mark}    Exception:"),
    Message.TEXT.name: (format_message, f"      ", f"\u270e   ", lambda line: True),
    Message.NOTE.name: (format_message, f"{mark}    [note]"),
    Message.DEBUG.name: (format_message, f"{mark}    [debug]"),
    Message.TRACE.name: (format_message, f"{mark}    [trace]"),
    Message.NONE.name: (format_message, "    "),
    Message.RESULT.name: (format_result, f"{result_mark} "),
}

def transform(show_input=True):
    """Transform parsed log line into a brisk format
    that is similar to nice but excludes step definitions
    and their attributes while keeping their core messages.
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
                        last_message[0] = msg
            else:
                line = None

        line = yield line
