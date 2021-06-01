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
import re

from testflows._core.contrib.arpeggio import RegExMatch as _
from testflows._core.contrib.arpeggio import OneOrMore, ZeroOrMore, EOF, Optional, Not
from testflows._core.contrib.arpeggio import ParserPython as PEGParser
from testflows._core.contrib.arpeggio import PTNodeVisitor, visit_parse_tree

class Visitor(PTNodeVisitor):
    def __init__(self, *args, **kwargs):
        self.header_ids = {}
        self.start_after = kwargs.pop("start_after", None)
        self.started = True
        if self.start_after is not None:
            self.started = False
        self.levels = []
        self.current_level = 0
        self.output = []
        super(Visitor, self).__init__(*args, **kwargs)

    def process_heading(self, node, children):
        level = node[0].value.count("#")
        # only include in TOC levels 2 and higher
        if level < 2:
            return None
        if not self.started:
            if self.start_after in node.heading_name.value:
                self.started = True
                return None
        if not self.started:
            return None
        # normalize header level
        level -= 1
        if self.current_level < level:
            self.levels = self.levels[:level - 1]
        if len(self.levels) < level:
            self.levels += [0] * (level - len(self.levels))
        self.current_level = level
        self.levels[self.current_level - 1] += 1
        num = '.'.join([str(l) for l in self.levels[:self.current_level]])
        return level, num

    def visit_heading(self, node, children):
        res = self.process_heading(node, children)
        if not res:
            return
        level, num = res
        name = node.heading_name.value
        anchor = re.sub(r"\s+", "-", re.sub(r"[^a-zA-Z0-9-_\s]+", "", name.lower()))
        # handle duplicate header ids
        if self.header_ids.get(anchor) is None:
            self.header_ids[anchor] = 1
        else:
            anchor = f"{anchor}{str(self.header_ids[anchor])}"
            self.header_ids[anchor] += 1
        indent = "  " * (level - 1)
        self.output.append(f"{indent}* {'.'.join([str(l) for l in self.levels[:self.current_level]])} [{name}](#{anchor})")

    def visit_document(self, node, children):
        self.output = "\n".join(self.output)
        if self.output:
            self.output += "\n"
        return self.output or None


class UpdateVisitor(PTNodeVisitor):
    def __init__(self, *args, **kwargs):
        self.heading = kwargs.pop("heading", None)
        self.toc = kwargs.pop("toc", "")
        self.output = []
        # states
        self.state_inside_toc = False
        self.state_done = False
        super(UpdateVisitor, self).__init__(*args, **kwargs)

    def visit_line(self, node, children):
        if not self.state_inside_toc:
            self.output.append(str(node))

    def visit_heading(self, node, children):
        self.output.append("".join(children))
        if not self.state_done and node.heading_name.value == self.heading:
            self.state_inside_toc = True
            self.output.append("\n")
            self.output.append(self.toc)
        else:
            if self.state_inside_toc:
                self.state_done = True
            self.state_inside_toc = False

    def visit_document(self, node, children):
        self.output = "".join(self.output)
        return self.output or None


def Parser():
    """Returns markdown heading parser.
    """
    def line():
        return _(r"[^\n]*\n")

    def heading():
        return [
            (_(r"\s*#+\s+"), heading_name, _(r"\n?")),
            (heading_name, _(r"\n?[-=]+\n?"))
        ]

    def heading_name():
        return _(r"[^\n]+")

    def document():
        return Optional(OneOrMore([heading, line])), EOF

    return PEGParser(document, skipws=False)


def generate(source, destination, heading, update=False):
    """Generate TOC for markdown source.

    :param source: source file-like object
    :param destination: destination file-like object
    :param heading: table of contents heading name
    :param update: write to destination source with the updated table of contents, default: False
    """
    parser = Parser()
    source_data = source.read()
    tree = parser.parse(source_data)
    toc = visit_parse_tree(tree, Visitor(start_after=heading))
    destination_data = ""
    if update:
        destination_data = visit_parse_tree(tree, UpdateVisitor(heading=heading, toc=toc))
    else:
        destination_data = toc
    if destination_data:
        destination.write(destination_data)
