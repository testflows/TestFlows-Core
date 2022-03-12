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
import textwrap
import functools

import testflows.settings as settings

from testflows._core.flags import Flags, SKIP, LAST_RETRY
from testflows._core.testtype import TestType, TestSubType
from testflows._core.message import Message
from testflows._core.objects import ExamplesTable
from testflows._core.name import split, parentname, basename
from testflows._core.cli.colors import color, cursor_up

indent = " " * 2
#: map of tests by name
tests_by_id = {}
#: map of tests by parent
tests_by_parent = {}
#: last message
last_message = [None]

def color_other(other, no_colors=False):
    return color(other, "white", attrs=["dim"], no_colors=no_colors)

def color_keyword(keyword, no_colors=False):
    return color(split(keyword)[-1], "white", attrs=["bold"], no_colors=no_colors)

def color_secondary_keyword(keyword, no_colors=False):
    return color(split(keyword)[-1], "white", attrs=["bold", "dim"], no_colors=no_colors)

def color_test_name(name, no_colors=False, use_full_testname=False):
    if use_full_testname:
        return color(name, "white", attrs=[], no_colors=no_colors)
    else:
        return color(split(name)[-1], "white", attrs=[], no_colors=no_colors)

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

def format_input(msg, keyword, no_colors=False):
    out = f"{indent * (msg['test_id'].count('/'))}"
    out += color("\u270b " + msg["message"], "yellow", attrs=["bold"], no_colors=no_colors) \
        + cursor_up(no_colors=no_colors) + "\n"
    return out

def format_prompt(msg, keyword, no_colors=False):
    lines = (msg["message"] or "").splitlines()
    icon = "\u270d  "
    if msg["message"].startswith("Paused"):
        icon = "\u270b "
    out = color(icon + lines[0], "yellow", attrs=["bold"], no_colors=no_colors)
    if len(lines) > 1:
        out += "\n" + color("\n".join(lines[1:]), "white", attrs=["dim"], no_colors=no_colors)
    return out

def format_input(msg, keyword, no_colors=False):
    out = color(msg['message'], "white", no_colors=no_colors) + "\n"
    return out

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
    return desc + "\n"

def format_specification(msg, no_colors=False):
    out = []
    _indent = indent * (msg["test_id"].count('/') - 1)

    if last_message[0] and not last_message[0]["message_keyword"] == Message.SPECIFICATION.name:
        out = [f"{_indent}{' ' * 2}{color_secondary_keyword('Specifications', no_colors=no_colors)}"]

    out.append(color(f"{_indent}{' ' * 4}{msg['specification_name']}", "white", attrs=["dim"], no_colors=no_colors))
    if msg["specification_version"]:
        out.append(color(f"{_indent}{' ' * 6}version {msg['specification_version']}", "white", attrs=["dim"], no_colors=no_colors))
    return "\n".join(out) + "\n"

def format_requirement(msg, no_colors=False):
    out = []
    _indent = indent * (msg["test_id"].count('/') - 1)

    if last_message[0] and not last_message[0]["message_keyword"] == Message.REQUIREMENT.name:
        out = [f"{_indent}{' ' * 2}{color_secondary_keyword('Requirements', no_colors=no_colors)}"]

    out.append(color(f"{_indent}{' ' * 4}{msg['requirement_name']}", "white", attrs=["dim"], no_colors=no_colors))
    out.append(color(f"{_indent}{' ' * 6}version {msg['requirement_version']}", "white", attrs=["dim"], no_colors=no_colors))
    return "\n".join(out) + "\n"

def format_attribute(msg, no_colors=False):
    out = []
    _indent = indent * (msg["test_id"].count('/') - 1)

    if last_message[0] and not last_message[0]["message_keyword"] == Message.ATTRIBUTE.name:
        out = [f"{_indent}{' ' * 2}{color_secondary_keyword('Attributes', no_colors=no_colors)}"]

    out.append(color(f"{_indent}{' ' * 4}{msg['attribute_name']}", "white", attrs=["dim"], no_colors=no_colors))
    out.append(color(f"{textwrap.indent(str(msg['attribute_value']), prefix=(_indent + ' ' * 6))}", "white", attrs=["dim"], no_colors=no_colors))
    return "\n".join(out) + "\n"

def format_tag(msg, no_colors=False):
    out = []
    _indent = indent * (msg["test_id"].count('/') - 1)

    if last_message[0] and not last_message[0]["message_keyword"] == Message.TAG.name:
        out = [f"{_indent}{' ' * 2}{color_secondary_keyword('Tags', no_colors=no_colors)}"]

    out.append(color(f"{_indent}{' ' * 4}{msg['tag_value']}", "white", attrs=["dim"], no_colors=no_colors))
    return "\n".join(out) + "\n"

def format_example(msg, no_colors=False):
    out = []
    _indent = indent * (msg["test_id"].count('/') - 1)

    row_format = msg["example_row_format"] or ExamplesTable.default_row_format(msg["example_columns"], msg["example_values"])
    if last_message[0] and not last_message[0]["message_keyword"] == Message.EXAMPLE.name:
        out = [f"{_indent}{' ' * 2}{color_secondary_keyword('Examples', no_colors=no_colors)}"]
        out.append(color(textwrap.indent(f"{ExamplesTable.__str_header__(tuple(msg['example_columns']),row_format)}",
            prefix=f"{_indent}{' ' * 4}"), "white", attrs=["dim"], no_colors=no_colors))

    out.append(color(textwrap.indent(f"{ExamplesTable.__str_row__(tuple(msg['example_values']),row_format)}",
        prefix=f"{_indent}{' ' * 4}"), "white", attrs=["dim"], no_colors=no_colors))
    return "\n".join(out) + "\n"

def format_argument(msg, no_colors=False):
    out = []
    _indent = indent * (msg["test_id"].count('/') - 1)

    if last_message[0] and not last_message[0]["message_keyword"] == Message.ARGUMENT.name:
        out = [f"{_indent}{' ' * 2}{color_secondary_keyword('Arguments', no_colors=no_colors)}"]

    out.append(color(f"{_indent}{' ' * 4}{msg['argument_name']}", "white", attrs=["dim"], no_colors=no_colors))
    out.append(color(textwrap.indent(f"{msg['argument_value']}",
        prefix=f"{_indent}{' ' * 6}"), "white", attrs=["dim"], no_colors=no_colors))
    return "\n".join(out) + "\n"

def get_type(msg):
    return getattr(TestType, msg["test_type"])

def get_subtype(msg):
    return getattr(TestSubType, str(msg["test_subtype"]), 0)

def and_keyword(msg, parent_id, keyword, subtype):
    """Handle processing of Given, When, Then, But, By and Finally
    keywords and convert them to And when necessary.
    """
    prev = tests_by_parent[parent_id][-2] if len(tests_by_parent.get(parent_id, [])) > 1 else None
    if prev and get_subtype(prev) == subtype and tests_by_parent.get(prev["test_id"]) is None:
        keyword = "And"
    parent = tests_by_id.get(parent_id)
    if parent and get_subtype(parent) == subtype and len(tests_by_parent.get(parent_id, [])) == 1:
        keyword = "And"
    return keyword

def format_test(msg, keyword, tests_by_parent, tests_by_id, no_colors=False):
    # add test to the tests map
    parent = parentname(msg["test_id"])
    if tests_by_parent.get(parent) is None:
        tests_by_parent[parent] = []
    tests_by_parent[parent].append(msg)
    tests_by_id[msg["test_id"]] = msg

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

    _keyword = color_keyword(keyword, no_colors=no_colors)
    _name = color_test_name(split(msg["test_name"])[-1], no_colors=no_colors)
    _indent = indent * (msg["test_id"].count('/') - 1)
    out = f"{_indent}{_keyword} {_name}\n"
    if msg["test_description"]:
        out += format_test_description(msg, _indent, no_colors=no_colors)
    return out

def format_result(msg, no_colors=False, use_indent=False, use_full_testname=False):
    result = msg["result_type"]
    _retry = get_type(msg) == TestType.RetryIteration and LAST_RETRY not in Flags(msg["test_flags"])
    _color = color_result(result, no_colors=no_colors, retry=_retry)
    _result = _color(result, no_colors=no_colors)
    if use_full_testname:
        _test = color_test_name(msg["result_test"],
                    no_colors=no_colors, use_full_testname=use_full_testname)
    else:
        _test = color_test_name(basename(msg["result_test"]), no_colors=no_colors)

    if use_indent is False:
        _indent = indent * (msg["test_id"].count('/') - 1)
    else:
        _indent = use_indent

    out = f"{_indent}{_result}"

    _result_message = msg["result_message"]
    if _result_message and settings.trim_results and int(msg["test_level"]) > 1:
        _result_message = _result_message.strip().split("\n",1)[0].strip()

    if result in ("Fail", "Error", "Null"):
        out += f" {_test}"
        if _result_message:
            out += color_test_name(",", no_colors=no_colors)
            out += f" {_color(format_multiline(_result_message, _indent).lstrip(), no_colors=no_colors)}"
    elif result.startswith("X"):
        out += f" {_test}"
        if msg["result_reason"]:
            out += color_test_name(",", no_colors=no_colors)
            out += f" {_color(msg['result_reason'], no_colors=no_colors)}"
    return out + "\n"

formatters = {
    Message.INPUT.name: (format_input, f""),
    Message.PROMPT.name: (format_prompt, f""),
    Message.TEST.name: (format_test, f"", tests_by_parent, tests_by_id),
    Message.RESULT.name: (format_result,),
    Message.ATTRIBUTE.name: (format_attribute,),
    Message.ARGUMENT.name: (format_argument,),
    Message.SPECIFICATION.name: (format_specification,),
    Message.REQUIREMENT.name: (format_requirement,),
    Message.TAG.name: (format_tag,),
    Message.EXAMPLE.name: (format_example,)
}

def transform(no_colors=False, show_input=True):
    """Transform parsed log line into a short format.
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
                        line = formatter[0](line, *formatter[1:], no_colors=no_colors)
                        last_message[0] = msg
            else:
                line = None
        line = yield line
