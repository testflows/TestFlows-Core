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

from testflows._core import __version__
from testflows._core.utils.strip import wstrip
from testflows._core.contrib.arpeggio import RegExMatch as _
from testflows._core.contrib.arpeggio import OneOrMore, ZeroOrMore, EOF, Optional, Not
from testflows._core.contrib.arpeggio import ParserPython as PEGParser
from testflows._core.contrib.arpeggio import PTNodeVisitor, visit_parse_tree

specification_template = """
%(pyname)s = Specification(
        name=%(name)s, 
        description=%(description)s,
        author=%(author)s,
        date=%(date)s, 
        status=%(status)s, 
        approved_by=%(approved_by)s,
        version=%(version)s,
        group=%(group)s,
        type=%(type)s,
        link=%(link)s,
        uid=%(uid)s,
        content=%(content)s)

"""

requirement_template = """
%(pyname)s = Requirement(
        name='%(name)s',
        version='%(version)s',
        priority=%(priority)s,
        group=%(group)s,
        type=%(type)s,
        uid=%(uid)s,
        description=%(description)s,
        link=%(link)s)

"""

class Visitor(PTNodeVisitor):
    def __init__(self, source_data, *args, **kwargs):
        self.source_data = source_data
        self.output = (
            "# These requirements were auto generated\n"
            "# from software requirements specification (SRS)\n"
            f"# document by TestFlows v{__version__}.\n"
            "# Do not edit by hand but re-generate instead\n"
            "# using \'tfs requirements generate\' command.\n"
            "from testflows.core import Specification\n"
            "from testflows.core import Requirement\n\n"
            )
        self.pyname_fmt = re.compile(r"[^a-zA-Z0-9]")
        super(Visitor, self).__init__(*args, **kwargs)

    def visit_line(self, node, children):
        pass

    def visit_specification(self, node, children):
        name = f"{node.specification_heading.specification_name.value.strip()}"
        pyname = re.sub(r"_+", "_", self.pyname_fmt.sub("_", name))
        author = None
        status = None
        version = None
        date = None
        approved_by = None
        description = None
        type = None
        group = None
        link = None
        uid = None

        try:
            author = f"'{str(node.author.words).strip()}'"
        except:
            pass
        try:
            status = f"'{str(node.approval.status.words).strip()}'"
        except:
            pass
        try:
            version = f"'{str(node.approval.approval_version.words).strip()}'"
        except:
            pass
        try:
            date = f"'{str(node.date.words).strip()}'"
        except:
            pass
        try:
            approved_by = f"'{str(node.approval.approved_by.words).strip()}'"
        except:
            pass

        self.output += specification_template.lstrip() % {
            "pyname": pyname,
            "name": f"'{name}'",
            "description": str(description),
            "author": str(author),
            "date": str(date),
            "status": str(status),
            "approved_by": str(approved_by),
            "version": str(version),
            "group": str(group),
            "type": str(type),
            "link": str(link),
            "uid": str(uid),
            "content": "'''\n%s\n'''" % self.source_data.replace("'''", "\'\'\'").rstrip()
        }

    def visit_requirement(self, node, children):
        name = node.requirement_heading.requirement_name.value
        pyname = re.sub(r"_+", "_", self.pyname_fmt.sub("_", name))
        description = None
        group = None
        priority = None
        type = None
        uid = None
        link = None

        try:
            description = "\n".join([f'{"":8}{repr(line.value)}' for lines in node.requirement_description for line in lines])
            description = wstrip(description, f"{'':8}'\\n'\n")
            description = f"(\n{description}\n{'':8})"
        except:
            pass
        try:
            priority = node.priority.word
        except:
            pass
        try:
            group = f"\"{node.group.word}\""
        except:
            pass
        try:
            type = f"\"{node.type.word}\""
        except:
            pass
        try:
            uid = f"\"{node.uid.word}\""
        except:
            pass

        self.output += requirement_template.lstrip() % {
            "pyname": pyname,
            "name": node.requirement_heading.requirement_name.value,
            "version": node.version.word,
            "description": str(description),
            "priority": str(priority),
            "group": str(group),
            "type": str(type),
            "uid": str(uid),
            "link": str(link)
        }

    def visit_document(self, node, children):
        return self.output.rstrip() + "\n"

def Parser():
    """Returns markdown requirements parser.
    """
    def line():
        return _(r"[^\n]*\n")

    def empty_line():
        return _(r"\s*\n")

    def not_heading():
        return Not(heading)

    def heading():
        return _(r"\s?\s?\s?#+\s+"), heading_name, _(r"\n")

    def requirement_heading():
        return _(r"\s?\s?\s?#+\s+"), requirement_name, _(r"\n")

    def specification_heading():
        return _(r"\s?\s?\s?#\s+"), specification_name, _(r"\n")

    def specification_approval_heading():
        return _(r"\s?\s?\s?#+\s+"), _(r"Approval"), _(r"\s*\n")

    def toc_heading():
        return _(r"\s?\s?\s?#+\s+"), _(r"Table of Contents"), _(r"\n")

    def specification_name():
        return _(r"(QA-)?SRS[^\n]+")

    def heading_name():
        return _(r"[^\n]+")

    def requirement_name():
        return _(r"RQ\.[^\n]+")

    def requirement_description():
        return ZeroOrMore((not_heading, line))

    def word():
        return _(r"[^\s]+")

    def words():
        return _(r"[^\n]+")

    def version():
        return _(r"\s*version:\s*"), word

    def priority():
        return _(r"\s*priority:\s*"), word

    def type():
        return _(r"\s*type:\s*"), word

    def group():
        return _(r"\s*group:\s*"), word

    def uid():
        return _(r"\s*uid:\s*"), word

    def other():
        return _(r"\*?\*?[^\*\n]+:\*?\*?\s*"), words, _(r"\n")

    def author():
        return _(r"\*?\*?[Aa]uthor:\*?\*?\s*"), words, _(r"\n")

    def date():
        return _(r"\*?\*?[Dd]ate:\*?\*?\s*"), words, _(r"\n")

    def status():
        return _(r"\*?\*?[Ss]tatus:\*?\*?\s*"), words, _(r"\n")

    def approval_version():
        return _(r"\*?\*?[Vv]ersion:\*?\*?\s*"), words, _(r"\n")

    def approved_by():
        return _(r"\*?\*?[Aa]pproved by:\*?\*?\s*"), words, _(r"\n")

    def approval():
        return specification_approval_heading, OneOrMore([
            status,
            approval_version,
            approved_by,
            date,
            empty_line
        ])

    def specification():
        return specification_heading, Optional(heading), OneOrMore([
            author,
            date,
            other,
            approval,
            empty_line,
            _(r"\s*[^\*#\n][^\n]*\n")
        ]), toc_heading

    def requirement():
        return requirement_heading, version, ZeroOrMore([priority, type, group, uid]), Optional(requirement_description), _(r"\n?")

    def document():
        return Optional(OneOrMore([specification, requirement, heading, line])), EOF

    return PEGParser(document, skipws=False)


def generate(source, destination):
    """Generate requirements from markdown source.

    :param source: source file-like object
    :param destination: destination file-like object
    """
    parser = Parser()
    source_data = source.read()
    tree = parser.parse(source_data)
    destination_data = visit_parse_tree(tree, Visitor(source_data=source_data))
    if destination_data:
        destination.write(destination_data)
