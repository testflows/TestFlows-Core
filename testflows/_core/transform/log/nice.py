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
import re
import textwrap

import testflows.settings as settings

from testflows._core.flags import Flags, SKIP
from testflows._core.testtype import TestType, TestSubType
from testflows._core.transform.log import message
from testflows._core.objects import ExamplesTable
from testflows._core.utils.timefuncs import strftime, strftimedelta
from testflows._core.utils.timefuncs import localfromtimestamp
from testflows._core.name import split, basename, parentname
from testflows._core.cli.colors import color, cursor_up

strip_nones = re.compile(r'( None)+$')
indent = " " * 2
#: map of tests by name
tests_by_name = {}
#: map of tests by parent
tests_by_parent = {}

def color_keyword(keyword):
    return color(split(keyword)[-1], "white", attrs=["bold"])

def color_secondary_keyword(keyword):
    return color(split(keyword)[-1], "white", attrs=["bold", "dim"])

def color_other(other):
    return color(other, "white", attrs=["dim"])

def color_result(prefix, result):
    if result.startswith("X"):
        return color(prefix + result, "blue", attrs=["bold"])
    elif result.endswith("OK"):
        return color(prefix + result, "green", attrs=["bold"])
    elif result.endswith("Skip"):
        return color(prefix + result, "cyan", attrs=["bold"])
    # Error, Fail, Null
    return color(prefix + result, "red", attrs=["bold"])

def format_input(msg, keyword):
    flags = Flags(msg.p_flags)
    if flags & SKIP and settings.show_skipped is False:
        return
    out = color_other(f"{strftimedelta(msg.p_time):>20}{'':3}{indent * (msg.p_id.count('/') - 1)}{keyword}")
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

def and_keyword(msg, parent_name, keyword, subtype):
    """Handle processing of Given, When, Then, But, By and Finally
    keywords and convert them to And when necessary.
    """
    prev = tests_by_parent[parent_name][-2] if len(tests_by_parent.get(parent_name, [])) > 1 else None
    if prev and prev.p_subtype == subtype and tests_by_parent.get(prev.p_id) is None:
        keyword = "And"
    parent = tests_by_name.get(parent_name)
    if parent and parent.p_subtype == subtype and len(tests_by_parent.get(parent_name, [])) == 1:
        keyword = "And"
    return keyword

def format_test(msg, keyword):
    flags = Flags(msg.p_flags)
    if flags & SKIP and settings.show_skipped is False:
        return

    # add test to the tests map
    parent = parentname(msg.p_id)
    if tests_by_parent.get(parent) is None:
        tests_by_parent[parent] = []
    tests_by_parent[parent].append(msg)
    tests_by_name[msg.p_id] = msg

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

    started = strftime(localfromtimestamp(msg.started))
    _keyword = color_keyword(keyword)
    _name = color_other(split(msg.name)[-1])
    _indent = f"{started:>20}" + f"{'':3}{indent * (msg.p_id.count('/') - 1)}"
    out = f"{color_other(_indent)}{_keyword} {_name}{color_other(', flags:' + str(flags) if flags else '')}\n"
    # convert indent to just spaces
    _indent = (len(_indent) + 3) * " "
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

def format_result_metrics(msg, indent):
    out = [f"{indent}{' ' * 2}{color_secondary_keyword('Metrics')}"]
    for metric in msg.metrics:
        out.append(color(f"{indent}{' ' * 4}{metric.name}", "white", attrs=["dim"]))
        out.append(color(textwrap.indent(f"{metric.value} {metric.units}", prefix=f"{indent}{' ' * 6}"), "white", attrs=["dim"]))
    return "\n".join(out) + "\n"

def format_result_values(msg, indent):
    out = [f"{indent}{' ' * 2}{color_secondary_keyword('Values')}"]
    for value in msg.values:
        out.append(color(f"{indent}{' ' * 4}{value.name}", "white", attrs=["dim"]))
        out.append(color(textwrap.indent(f"{value.value}", prefix=f"{indent}{' ' * 6}"), "white", attrs=["dim"]))
    return "\n".join(out) + "\n"

def format_result_tickets(msg, indent):
    out = [f"{indent}{' ' * 2}{color_secondary_keyword('Tickets')}"]
    for ticket in msg.tickets:
        out.append(color(f"{indent}{' ' * 4}{ticket.name}", "white", attrs=["dim"]))
        out.append(color(textwrap.indent(f"{ticket.link}", prefix=f"{indent}{' ' * 6}"), "white", attrs=["dim"]))
    return "\n".join(out) + "\n"

def format_result(msg, prefix, result):
    if Flags(msg.p_flags) & SKIP and settings.show_skipped is False:
        return
    _result = color_result(prefix, result)
    _test = color_other(basename(msg.test))
    _indent = f"{strftimedelta(msg.p_time):>20}" + f"{'':3}{indent * (msg.p_id.count('/') - 1)}"

    out = (f"{color_other(_indent)}{_result} "
        f"{_test}{color_other(', ' + msg.test)}"
        f"{(color_other(', ') + color(format_multiline(msg.message, _indent + ' ' * 26).lstrip(), 'yellow', attrs=['bold'])) if msg.message else ''}"
        f"{(color_other(', ') + color(msg.reason, 'blue', attrs=['bold'])) if msg.reason else ''}\n")

    # convert indent to just spaces
    #_indent = (len(_indent) + 3) * " "
    #if msg.metrics:
    #    out += format_result_metrics(msg, _indent)
    #if msg.tickets:
    #    out += format_result_tickets(msg, _indent)
    #if msg.values:
    #    out += format_result_values(msg, _indent)
    return out

def format_other(msg, keyword):
    if Flags(msg.p_flags) & SKIP and settings.show_skipped is False:
        return
    fields = ' '.join([str(f) for f in msg[message.Prefix.time + 1:]])
    if msg.p_stream:
        fields = f"[{msg.p_stream}] {fields}"
    fields = strip_nones.sub("", fields)

    fields = textwrap.indent(fields, prefix=(indent * (msg.p_id.count('/') - 1) + " " * 30))
    fields = fields.lstrip(" ")

    return color_other(f"{strftimedelta(msg.p_time):>20}{'':3}{indent * (msg.p_id.count('/') - 1)}{keyword} {color_other(fields)}\n")

def format_metric(msg, keyword):
    if Flags(msg.p_flags) & SKIP and settings.show_skipped is False:
        return
    prefix = f"{strftimedelta(msg.p_time):>20}" + f"{'':3}{indent * (msg.p_id.count('/') - 1)}"
    _indent = (len(prefix) + 3) * " "
    out = [color_other(f"{prefix}{keyword}") + color("Metric", "white", attrs=["dim", "bold"]) + color_other(f" {msg.name}")]
    out.append(color_other(format_multiline(f"{msg.value} {msg.units}", _indent + " " * 2)))
    return "\n".join(out) + "\n"

def format_value(msg, keyword):
    if Flags(msg.p_flags) & SKIP and settings.show_skipped is False:
        return
    prefix = f"{strftimedelta(msg.p_time):>20}" + f"{'':3}{indent * (msg.p_id.count('/') - 1)}"
    _indent = (len(prefix) + 3) * " "
    out = [color_other(f"{prefix}{keyword}") + color("Value", "white", attrs=["dim", "bold"]) + color_other(f" {msg.name}")]
    out.append(color_other(format_multiline(f"{msg.value}", _indent + " " * 2)))
    return "\n".join(out) + "\n"

def format_ticket(msg, keyword):
    if Flags(msg.p_flags) & SKIP and settings.show_skipped is False:
        return
    prefix = f"{strftimedelta(msg.p_time):>20}" + f"{'':3}{indent * (msg.p_id.count('/') - 1)}"
    _indent = (len(prefix) + 3) * " "
    out = [color_other(f"{prefix}{keyword}") + color("Ticket", "white", attrs=["dim", "bold"]) + color_other(f" {msg.name}")]
    out.append(color_other(format_multiline(f"{msg.link}", _indent + " " * 2)))
    return "\n".join(out) + "\n"

mark = "\u27e5"
result_mark = "\u27e5\u27e4"

formatters = {
    message.RawInput: (format_input, f"{mark} "),
    message.RawTest: (format_test, f"{mark}  "),
    message.RawDescription: (format_other, f"{mark}    :"),
    message.RawArgument: (format_other, f"{mark}    @"),
    message.RawAttribute: (format_other, f"{mark}    -"),
    message.RawRequirement: (format_other, f"{mark}    ?"),
    message.RawValue: (format_value, f"{mark}    "),
    message.RawMetric: (format_metric, f"{mark}    "),
    message.RawTicket: (format_ticket, f"{mark}    "),
    message.RawException: (format_other, f"{mark}    Exception:"),
    message.RawNote: (format_other, f"{mark}    [note]"),
    message.RawDebug: (format_other, f"{mark}    [debug]"),
    message.RawTrace: (format_other, f"{mark}    [trace]"),
    message.RawNone: (format_other, "    "),
    message.RawResultOK: (format_result, f"{result_mark} ", "OK"),
    message.RawResultFail: (format_result, f"{result_mark} ", "Fail"),
    message.RawResultError: (format_result, f"{result_mark} ", "Error"),
    message.RawResultSkip: (format_result, f"{result_mark} ", "Skip"),
    message.RawResultNull: (format_result, f"{result_mark} ", "Null"),
    message.RawResultXOK: (format_result, f"{result_mark} ", "XOK"),
    message.RawResultXFail: (format_result, f"{result_mark} ", "XFail"),
    message.RawResultXError: (format_result, f"{result_mark} ", "XError"),
    message.RawResultXNull: (format_result, f"{result_mark} ", "XNull")
}

def transform(stop):
    """Transform parsed log line into a nice format.

    :param stop: stop event
    """
    line = None

    while True:
        if line is not None:
            msg = line
            formatter = formatters.get(type(line), None)
            if formatter:
                line = formatter[0](line, *formatter[1:])
            else:
                line = None

        line = yield line
