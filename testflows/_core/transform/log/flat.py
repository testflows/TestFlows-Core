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

from testflows._core.flags import Flags, SKIP, LAST_RETRY
from testflows._core.testtype import TestType, TestSubType
from testflows._core.message import Message
from testflows._core.objects import ExamplesTable
from testflows._core.name import split, parentname, basename
from testflows._core.cli.colors import color

indent = " " * 2
#: last message
last_message = [None]

def color_other(other, no_colors=False):
    return color(other, "white", attrs=["dim"], no_colors=no_colors)

def color_keyword(keyword, no_colors=False):
    return color(split(keyword)[-1], "white", attrs=["bold"], no_colors=no_colors)

def color_secondary_keyword(keyword, no_colors=False):
    return color(split(keyword)[-1], "white", attrs=["bold", "dim"], no_colors=no_colors)

def color_test_name(name, no_colors=False):
    return color(name, "white", attrs=[], no_colors=no_colors)

def color_result(result, attrs=None, no_colors=False, retry=False):
    if attrs is None:
        attrs = ["bold"]
    if result.startswith("X"):
        return functools.partial(color, color="blue", attrs=attrs, no_colors=no_colors)
    elif result == "OK":
        return functools.partial(color, color="green", attrs=attrs, no_colors=no_colors)
    elif result == "Skip":
        return functools.partial(color, color="cyan", attrs=attrs, no_colors=no_colors)
    elif retry:
        return functools.partial(color, color="cyan", attrs=attrs, no_colors=no_colors)
    elif result == "Error":
        return functools.partial(color, color="yellow", attrs=attrs, no_colors=no_colors)
    elif result == "Fail":
        return functools.partial(color, color="red", attrs=attrs, no_colors=no_colors)
    elif result == "Null":
        return functools.partial(color, color="magenta", attrs=attrs, no_colors=no_colors)
    else:
        raise ValueError(f"unknown result {result}")

def format_multiline(text, indent):
    first, rest = (text.rstrip() + "\n").split("\n", 1)
    first = first.strip()
    if first:
        first += "\n"
    out = f"{first}{textwrap.dedent(rest.rstrip())}".rstrip()
    out = textwrap.indent(out, indent + "  ")
    return out

def format_test_description(msg, indent, no_colors=False):
    desc = format_multiline(msg["test_description"], indent)
    desc = color(desc, "white", attrs=["dim"], no_colors=no_colors)
    return desc

def format_specification(msg, no_colors=False):
    out = []
    _indent = indent

    if not last_message[0] or (last_message[0] and last_message[0]["test_name"] != msg["test_name"]):
        out.append(format_test(msg, keyword="", no_colors=no_colors))

    if not last_message[0] or (last_message[0] and not last_message[0]["message_keyword"] == Message.SPECIFICATION.name or last_message[0]["test_name"] != msg["test_name"]):
        out.append(f"{_indent}{' ' * 0}{color_secondary_keyword('Specifications', no_colors=no_colors)}")

    out.append(color(f"{_indent}{' ' * 2}{msg['specification_name']}", "white", attrs=["dim"], no_colors=no_colors))
    if msg["specification_version"]:
        out.append(color(f"{_indent}{' ' * 4}version {msg['specification_version']}", "white", attrs=["dim"], no_colors=no_colors))
    return "\n".join(out) + "\n"

def format_requirement(msg, no_colors=False):
    out = []
    _indent = indent

    if not last_message[0] or (last_message[0] and last_message[0]["test_name"] != msg["test_name"]):
        out.append(format_test(msg, keyword="", no_colors=no_colors))

    if not last_message[0] or (last_message[0] and not last_message[0]["message_keyword"] == Message.REQUIREMENT.name or last_message[0]["test_name"] != msg["test_name"]):
        out.append(f"{_indent}{' ' * 0}{color_secondary_keyword('Requirements', no_colors=no_colors)}")

    out.append(color(f"{_indent}{' ' * 2}{msg['requirement_name']}", "white", attrs=["dim"], no_colors=no_colors))
    out.append(color(f"{_indent}{' ' * 4}version {msg['requirement_version']}", "white", attrs=["dim"], no_colors=no_colors))
    return "\n".join(out) + "\n"

def format_attribute(msg, no_colors=False):
    out = []
    _indent = indent

    if not last_message[0] or (last_message[0] and last_message[0]["test_name"] != msg["test_name"]):
        out.append(format_test(msg, keyword="", no_colors=no_colors))

    if not last_message[0] or (last_message[0] and not last_message[0]["message_keyword"] == Message.ATTRIBUTE.name or last_message[0]["test_name"] != msg["test_name"]):
        out.append(f"{_indent}{' ' * 0}{color_secondary_keyword('Attributes', no_colors=no_colors)}")

    out.append(color(f"{_indent}{' ' * 2}{msg['attribute_name']}", "white", attrs=["dim"], no_colors=no_colors))
    out.append(color(f"{textwrap.indent(str(msg['attribute_value']), prefix=(_indent + ' ' * 6))}", "white", attrs=["dim"], no_colors=no_colors))
    return "\n".join(out) + "\n"

def format_tag(msg, no_colors=False):
    out = []
    _indent = indent

    if not last_message[0] or (last_message[0] and last_message[0]["test_name"] != msg["test_name"]):
        out.append(format_test(msg, keyword="", no_colors=no_colors))

    if not last_message[0] or (last_message[0] and (not last_message[0]["message_keyword"] == Message.TAG.name or last_message[0]["test_name"] != msg["test_name"])):
        out.append(f"{_indent}{' ' * 0}{color_secondary_keyword('Tags', no_colors=no_colors)}")

    out.append(color(f"{_indent}{' ' * 2}{msg['tag_value']}", "white", attrs=["dim"], no_colors=no_colors))
    return "\n".join(out) + "\n"

def format_metric(msg, no_colors=False):
    out = []
    _indent = indent

    if not last_message[0] or (last_message[0] and last_message[0]["test_name"] != msg["test_name"]):
        out.append(format_test(msg, keyword="", no_colors=no_colors))

    out.append(
        color_other(f"{_indent}", no_colors=no_colors)
        + color("Metric", "white", attrs=["dim", "bold"], no_colors=no_colors)
        + color_other(f" {msg['metric_name']}", no_colors=no_colors)
    )
    out.append(color_other(format_multiline(f"{msg['metric_value']} {msg['metric_units']}", _indent), no_colors=no_colors))
    return "\n".join(out) + "\n"

def format_example(msg, no_colors=False):
    out = []
    _indent = indent

    if not last_message[0] or (last_message[0] and last_message[0]["test_name"] != msg["test_name"]):
        out.append(format_test(msg, keyword="", no_colors=no_colors))

    row_format = msg["example_row_format"] or ExamplesTable.default_row_format(msg["example_columns"], msg["example_values"])

    if not last_message[0] or (last_message[0] and not last_message[0]["message_keyword"] == Message.EXAMPLE.name or last_message[0]["test_name"] != msg["test_name"]):
        out.append(f"{_indent}{' ' * 0}{color_secondary_keyword('Examples', no_colors=no_colors)}")
        out.append(color(textwrap.indent(f"{ExamplesTable.__str_header__(tuple(msg['example_columns']),row_format)}",
            prefix=f"{_indent}{' ' * 2}"), "white", attrs=["dim"], no_colors=no_colors))

    out.append(color(textwrap.indent(f"{ExamplesTable.__str_row__(tuple(msg['example_values']),row_format)}",
        prefix=f"{_indent}{' ' * 2}"), "white", attrs=["dim"], no_colors=no_colors))
    return "\n".join(out) + "\n"

def format_argument(msg, no_colors=False):
    out = []
    _indent = indent

    if not last_message[0] or (last_message[0] and last_message[0]["test_name"] != msg["test_name"]):
        out.append(format_test(msg, keyword="", no_colors=no_colors))

    if not last_message[0] or (last_message[0] and not last_message[0]["message_keyword"] == Message.ARGUMENT.name or last_message[0]["test_name"] != msg["test_name"]):
        out.append(f"{_indent}{' ' * 0}{color_secondary_keyword('Arguments', no_colors=no_colors)}")

    out.append(color(f"{_indent}{' ' * 2}{msg['argument_name']}", "white", attrs=["dim"], no_colors=no_colors))
    out.append(color(textwrap.indent(f"{msg['argument_value']}",
        prefix=f"{_indent}{' ' * 4}"), "white", attrs=["dim"], no_colors=no_colors))
    return "\n".join(out) + "\n"

def get_type(msg):
    return getattr(TestType, msg["test_type"])

def get_subtype(msg):
    return getattr(TestSubType, str(msg["test_subtype"]), 0)

def format_test(msg, keyword, no_colors=False):
    test_type = get_type(msg)
    test_subtype = get_subtype(msg)

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
        if test_subtype == TestSubType.Paragraph:
            keyword += "Paragraph"
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

    _keyword = color_keyword(f"{keyword}", no_colors=no_colors)
    _name = color_test_name(msg["test_name"], no_colors=no_colors)
    _indent = ""
    out = f"{_indent}{_keyword} {_name}"
    if msg.get("test_description"):
        out += "\n" + format_test_description(msg, _indent, no_colors=no_colors)
    if msg["message_keyword"] == Message.TEST.name:
        out += "\n"
    return out

def format_result(msg, no_colors=False):
    result = msg["result_type"]
    _retry = get_type(msg) == TestType.RetryIteration and LAST_RETRY not in Flags(msg["test_flags"])
    _color = color_result(result, no_colors=no_colors, retry=_retry)
    _result = _color(result, no_colors=no_colors)
    _test = color_test_name(msg["result_test"], no_colors=no_colors)

    _indent = ""
    out = ""

    if not last_message[0] or (last_message[0] and last_message[0]["test_name"] != msg["test_name"]):
        out += format_test(msg, keyword="", no_colors=no_colors) + "\n"

    out += f"{_indent}{_result} "

    if result in ("Fail", "Error", "Null"):
        out += f" {_test}"
        if msg["result_message"]:
            out += color_test_name(",", no_colors=no_colors)
            out += f" {_color(format_multiline(msg['result_message'], _indent).lstrip(), no_colors=no_colors)}"
    elif result.startswith("X"):
        out += f" {_test}"
        if msg["result_reason"]:
            out += color_test_name(",", no_colors=no_colors)
            out += f" {_color(msg['result_reason'], no_colors=no_colors)}"
    return out + "\n"

formatters = {
    Message.TEST.name: (format_test, f""),
    Message.RESULT.name: (format_result,),
    Message.ATTRIBUTE.name: (format_attribute,),
    Message.ARGUMENT.name: (format_argument,),
    Message.SPECIFICATION.name: (format_specification,),
    Message.REQUIREMENT.name: (format_requirement,),
    Message.TAG.name: (format_tag,),
    Message.METRIC.name: (format_metric,),
    Message.EXAMPLE.name: (format_example,)
}

def transform(no_colors=False, show_input=True):
    """Transform parsed log line into a flat format.
    """
    line = None
    while True:
        if line is not None:
            msg = line
            formatter = formatters.get(line["message_keyword"], None)
            if formatter:
                flags = Flags(line["test_flags"])
                if flags & SKIP and settings.show_skipped is False:
                    line = None
                else:
                    line = formatter[0](line, *formatter[1:], no_colors=no_colors)
                    last_message[0] = msg
            else:
                line = None
        line = yield line
