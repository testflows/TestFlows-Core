# Copyright 2019 Vitaliy Zakaznikov (TestFlows Test Framework http://testflows.com)
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

import testflows.settings as settings

from testflows._core.flags import Flags, SKIP
from testflows._core.testtype import TestType, TestSubType
from testflows._core.transform.log import message
from testflows._core.objects import ExamplesTable
from testflows._core.name import split, parentname, basename
from testflows._core.cli.colors import color, cursor_up

indent = " " * 2
#: map of tests by name
tests_by_id = {}
#: map of tests by parent
tests_by_parent = {}

def color_other(other):
    return color(other, "white", attrs=["dim"])

def color_keyword(keyword):
    return color(split(keyword)[-1], "white", attrs=["bold"])

def color_secondary_keyword(keyword):
    return color(split(keyword)[-1], "white", attrs=["bold", "dim"])

def color_test_name(name):
    return color(split(name)[-1], "white", attrs=[])

def color_result(result):
    if result.startswith("X"):
        return color(result, "blue", attrs=["bold"])
    elif result == "OK":
        return color(result, "green", attrs=["bold"])
    elif result == "Skip":
        return color(result, "cyan", attrs=["bold"])
    # Error, Fail, Null
    return color(result, "red", attrs=["bold"])

def format_input(msg, keyword):
    flags = Flags(msg.p_flags)
    if flags & SKIP and settings.show_skipped is False:
        return
    out = f"{indent * (msg.p_id.count('/'))}"
    out += color("\u270b " + msg.message, "yellow", attrs=["bold"]) + cursor_up() + "\n"
    return out

def format_multiline(text, indent):
    first, rest = (text.rstrip() + "\n").split("\n", 1)
    first = first.strip()
    if first:
        first += "\n"
    out = f"{first}{textwrap.dedent(rest.rstrip())}".rstrip()
    out = textwrap.indent(out, indent + "  ")
    return out

def format_description(msg, indent):
    desc = format_multiline(msg.description.description, indent)
    desc = color(desc, "white", attrs=["dim"])
    return desc + "\n"

def format_requirements(msg, indent):
    out = [f"{indent}{' ' * 2}{color_secondary_keyword('Requirements')}"]
    for req in msg.requirements:
        out.append(color(f"{indent}{' ' * 4}{req.name}", "white", attrs=["dim"]))
        out.append(color(f"{indent}{' ' * 6}version {req.version}", "white", attrs=["dim"]))
    return "\n".join(out) + "\n"

def format_attributes(msg, indent):
    out = [f"{indent}{' ' * 2}{color_secondary_keyword('Attributes')}"]
    for attr in msg.attributes:
        out.append(color(f"{indent}{' ' * 4}{attr.name}", "white", attrs=["dim"]))
        out.append(color(f"{indent}{' ' * 6}{attr.value}", "white", attrs=["dim"]))
    return "\n".join(out) + "\n"

def format_tags(msg, indent):
    out = [f"{indent}{' ' * 2}{color_secondary_keyword('Tags')}"]
    for tag in msg.tags:
        out.append(color(f"{indent}{' ' * 4}{tag.value}", "white", attrs=["dim"]))
    return "\n".join(out) + "\n"

def format_examples(msg, indent):
    examples = ExamplesTable(*msg.examples)
    out = [f"{indent}{' ' * 2}{color_secondary_keyword('Examples')}"]
    out.append(color(textwrap.indent(f"{examples}", prefix=f"{indent}{' ' * 4}"), "white", attrs=["dim"]))
    return "\n".join(out) + "\n"

def format_arguments(msg, indent):
    out = [f"{indent}{' ' * 2}{color_secondary_keyword('Arguments')}"]
    for arg in msg.args:
        out.append(color(f"{indent}{' ' * 4}{arg.name}", "white", attrs=["dim"]))
        out.append(color(textwrap.indent(f"{arg.value}", prefix=f"{indent}{' ' * 6}"), "white", attrs=["dim"]))
    return "\n".join(out) + "\n"

def format_users(msg, indent):
    out = [f"{indent}{' ' * 2}{color_secondary_keyword('Users')}"]
    for user in msg.users:
        out.append(color(f"{indent}{' ' * 4}{user.name}", "white", attrs=["dim"]))
    return "\n".join(out) + "\n"

def format_tickets(msg, indent):
    out = [f"{indent}{' ' * 2}{color_secondary_keyword('Tickets')}"]
    for ticket in msg.tickets:
        out.append(color(f"{indent}{' ' * 4}{ticket.name}", "white", attrs=["dim"]))
    return "\n".join(out) + "\n"

def and_keyword(msg, parent_id, keyword, subtype):
    """Handle processing of Given, When, Then, But, By and Finally
    keywords and convert them to And when necessary.
    """
    prev = tests_by_parent[parent_id][-2] if len(tests_by_parent.get(parent_id, [])) > 1 else None
    if prev and prev.p_subtype == subtype and tests_by_parent.get(prev.p_id) is None:
        keyword = "And"
    parent = tests_by_id.get(parent_id)
    if parent and parent.p_subtype == subtype and len(tests_by_parent.get(parent_id, [])) == 1:
        keyword = "And"
    return keyword

def format_test(msg, keyword, tests_by_parent, tests_by_id):
    flags = Flags(msg.p_flags)
    if flags & SKIP and settings.show_skipped is False:
        return

    # add test to the tests map
    parent = parentname(msg.p_id)
    if tests_by_parent.get(parent) is None:
        tests_by_parent[parent] = []
    tests_by_parent[parent].append(msg)
    tests_by_id[msg.p_id] = msg

    if msg.p_type == TestType.Module:
        keyword += "Module"
    elif msg.p_type == TestType.Suite:
        if msg.p_subtype == TestSubType.Feature:
            keyword += "Feature"
        else:
            keyword += "Suite"
    elif msg.p_type == TestType.Iteration:
        keyword += "Iteration"
    elif msg.p_type == TestType.Step:
        if msg.p_subtype == TestSubType.And:
            keyword += "And"
        elif msg.p_subtype == TestSubType.Given:
            keyword += and_keyword(msg, parent, "Given", TestSubType.Given)
        elif msg.p_subtype == TestSubType.When:
            keyword += and_keyword(msg, parent, "When", TestSubType.When)
        elif msg.p_subtype == TestSubType.Then:
            keyword += and_keyword(msg, parent, "Then", TestSubType.Then)
        elif msg.p_subtype == TestSubType.By:
            keyword += and_keyword(msg, parent, "By", TestSubType.By)
        elif msg.p_subtype == TestSubType.But:
            keyword += and_keyword(msg, parent, "But", TestSubType.But)
        elif msg.p_subtype == TestSubType.Finally:
            keyword += and_keyword(msg, parent, "Finally", TestSubType.Finally)
        else:
            keyword += "Step"
    else:
        if msg.p_subtype == TestSubType.Scenario:
            keyword += "Scenario"
        elif msg.p_subtype == TestSubType.Background:
            keyword += "Background"
        else:
            keyword += "Test"

    _keyword = color_keyword(keyword)
    _name = color_test_name(split(msg.name)[-1])
    _indent = indent * (msg.p_id.count('/') - 1)
    out = f"{_indent}{_keyword} {_name}\n"
    if msg.description:
        out += format_description(msg, _indent)
    if msg.tags:
        out += format_tags(msg, _indent)
    if msg.requirements:
        out += format_requirements(msg, _indent)
    if msg.attributes:
        out += format_attributes(msg, _indent)
    if msg.users:
        out += format_users(msg, _indent)
    if msg.tickets:
        out += format_tickets(msg, _indent)
    if msg.args:
        out += format_arguments(msg, _indent)
    if msg.examples:
        out += format_examples(msg, _indent)
    return out

def format_result(msg, result):
    flags = Flags(msg.p_flags)
    if flags & SKIP and settings.show_skipped is False:
        return

    _result = color_result(result)
    _test = color_test_name(basename(msg.test))

    _indent = indent * (msg.p_id.count('/') - 1)
    out = f"{_indent}{_result}"

    if msg.name in ("Fail", "Error", "Null"):
        out += f" {_test}"
        if msg.message:
            out += color_test_name(",")
            out += f" {color(format_multiline(msg.message, _indent).lstrip(), 'yellow', attrs=['bold'])}"
    elif msg.name.startswith("X"):
        out += f" {_test}"
        if msg.reason:
            out += color_test_name(",")
            out += f" {color(msg.reason, 'blue', attrs=['bold'])}"
    return out + "\n"

formatters = {
    message.RawInput: (format_input, f""),
    message.RawTest: (format_test, f"", tests_by_parent, tests_by_id),
    message.RawResultOK: (format_result, f"OK"),
    message.RawResultFail: (format_result, f"Fail"),
    message.RawResultError: (format_result, f"Error"),
    message.RawResultSkip: (format_result, f"Skip"),
    message.RawResultNull: (format_result, f"Null"),
    message.RawResultXOK: (format_result, f"XOK"),
    message.RawResultXFail: (format_result, f"XFail"),
    message.RawResultXError: (format_result, f"XError"),
    message.RawResultXNull: (format_result, f"XNull")
}

def transform():
    """Transform parsed log line into a short format.
    """
    line = None
    while True:
        if line is not None:
            formatter = formatters.get(type(line), None)
            if formatter:
                line = formatter[0](line, *formatter[1:])
            else:
                line = None
        line = yield line