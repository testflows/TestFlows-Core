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
        approved_date=%(approved_date)s,
        approved_version=%(approved_version)s,
        version=%(version)s,
        group=%(group)s,
        type=%(type)s,
        link=%(link)s,
        uid=%(uid)s,
        parent=%(parent)s,
        children=%(children)s,
        content=%(content)s)

"""

requirement_template = """
%(pyname)s = Requirement(
        name=%(name)s,
        version=%(version)s,
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
        name = str(node.specification_heading.specification_name.value).strip()
        pyname = re.sub(r"_+", "_", self.pyname_fmt.sub("_", name))
        author = None
        status = None
        version = None
        date = None
        approved_by = None
        approved_date = None
        approved_version = None
        description = None
        type = None
        group = None
        link = None
        uid = None
        parent = None
        children = None

        try:
            date = str(node.specification_date.words).strip()
        except:
            pass
        try:
            author = str(node.specification_author.words).strip()
        except:
            pass
        try:
            version = str(node.specification_version.words).strip()
        except:
            pass
        try:
            status = str(node.specification_approval.specification_approval_status.words).strip()
        except:
            pass
        try:
            approved_version = str(node.specification_approval.specification_approval_version.words).strip()
        except:
            pass
        try:
            approved_date = str(node.specification_approval.specification_approval_date.words).strip()
        except:
            pass
        try:
            approved_by = str(node.specification_approval.specification_approval_by.words).strip()
        except:
            pass

        self.output += specification_template.lstrip() % {
            "pyname": pyname,
            "name": repr(name),
            "description": repr(description),
            "author": repr(author),
            "date": repr(date),
            "status": repr(status),
            "approved_by": repr(approved_by),
            "approved_date": repr(approved_date),
            "approved_version": repr(approved_version),
            "version": repr(version),
            "group": repr(group),
            "type": repr(type),
            "link": repr(link),
            "uid": repr(uid),
            "parent": repr(parent),
            "children": repr(children),
            "content": "'''\n%s\n'''" % self.source_data.replace("'''", "\'\'\'").rstrip()
        }

    def visit_requirement(self, node, children):
        name = node.requirement_heading.requirement_name.value
        version = str(node.requirement_version.word)
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
            description = "None"
        try:
            priority = str(node.requirement_priority.word)
        except:
            pass
        try:
            group = str(node.requirement_group.word)
        except:
            pass
        try:
            type = str(node.requirement_type.word)
        except:
            pass
        try:
            uid = str(node.requirement_uid.word)
        except:
            pass

        self.output += requirement_template.lstrip() % {
            "pyname": pyname,
            "name": repr(name),
            "version": repr(version),
            "description": description,
            "priority": repr(priority),
            "group": repr(group),
            "type": repr(type),
            "uid": repr(uid),
            "link": repr(link)
        }

    def visit_document(self, node, children):
        return self.output.rstrip() + "\n"

def Parser():
    """Returns markdown requirements parser.
    """
    def line():
        return _(r"[^\n]*\n?")

    def empty_line():
        return _(r"[ \t]*\n")

    def heading():
        return _(r"#+[ \t]+"), heading_name, _(r"\n")

    def toc_heading():
        return _(r"#+[ \t]+"), _(r"Table of Contents"), _(r"[ \t]*\n")

    def heading_name():
        return _(r"[^\n]+")

    def not_heading():
        return Not(heading)

    def word():
        return _(r"[^\s]+")

    def words():
        return _(r"[^\n]+")

    def requirement_name():
        return _(r"RQ\.[^\n]+")

    def requirement_description():
        return ZeroOrMore((not_heading, line))

    def requirement_heading():
        return _(r"#+[ \t]+"), requirement_name, _(r"\n")

    def requirement_version():
        return _(r"[ \t]*version:[ \t]*"), word

    def requirement_priority():
        return _(r"[ \t]*priority:[ \t]*"), word

    def requirement_type():
        return _(r"[ \t]*type:[ \t]*"), word

    def requirement_group():
        return _(r"[ \t]*group:[ \t]*"), word

    def requirement_uid():
        return _(r"[ \t]*uid:[ \t]*"), word

    def specification_name():
        return _(r"(QA-)?SRS[^\n]+")

    def specification_heading():
        return _(r"#[ \t]+"), specification_name, _(r"\n")

    def specification_author():
        return _(r"\*?\*?[Aa]uthor:\*?\*?[ \t]*"), words, _(r"\n")

    def specification_date():
        return _(r"\*?\*?[Dd]ate:\*?\*?[ \t]*"), words, _(r"\n")

    def specification_version():
        return _(r"\*?\*?[Vv]ersion:\*?\*?[ \t]*"), words, _(r"\n")

    def specification_other():
        return _(r"\*?\*?[^\*\n]+:\*?\*?[ \t]*"), words, _(r"\n")

    def specification_approval_heading():
        return _(r"#+[ \t]+"), _(r"Approval"), _(r"[ \t]*\n")

    def specification_approval_status():
        return _(r"\*?\*?[Ss]tatus:\*?\*?[ \t]*"), words, _(r"\n")

    def specification_approval_version():
        return _(r"\*?\*?[Vv]ersion:\*?\*?[ \t]*"), words, _(r"\n")

    def specification_approval_by():
        return _(r"\*?\*?[Aa]pproved by:\*?\*?[ \t]*"), words, _(r"\n")

    def specification_approval_date():
        return _(r"\*?\*?[Dd]ate:\*?\*?[ \t]*"), words, _(r"\n")

    def specification_approval_other():
        return _(r"\*?\*?[^\*\n]+:\*?\*?[ \t]*"), words, _(r"\n")

    def specification_approval():
        return specification_approval_heading, ZeroOrMore([
            specification_approval_status,
            specification_approval_version,
            specification_approval_by,
            specification_approval_date,
            specification_approval_other,
            empty_line
        ])

    def specification():
        return specification_heading, ZeroOrMore(heading), ZeroOrMore([
            specification_author,
            specification_date,
            specification_version,
            specification_other,
            specification_approval,
            empty_line,
            _(r"[ \t]*[^\*#\n][^\n]*\n")
        ]), toc_heading

    def requirement():
        return requirement_heading, requirement_version, ZeroOrMore([
                requirement_priority, requirement_type, requirement_group, requirement_uid
            ]), Optional(requirement_description)

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
