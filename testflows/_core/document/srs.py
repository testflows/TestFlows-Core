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

from collections import namedtuple

from testflows._core import __version__
from testflows._core.utils.strip import wstrip
from testflows._core.contrib.arpeggio import RegExMatch as _
from testflows._core.contrib.arpeggio import OneOrMore, ZeroOrMore, EOF, Optional, Not
from testflows._core.contrib.arpeggio import ParserPython as PEGParser
from testflows._core.contrib.arpeggio import PTNodeVisitor, visit_parse_tree
from testflows._core.objects import Specification, Requirement

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
    headings=%(headings)s,
    requirements=%(requirements)s,
    content=%(content)s
)
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
    link=%(link)s,
    level=%(level)s,
    num=%(num)s
)

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
            "Heading = Specification.Heading\n\n"
            )
        self.levels = [0]
        self.current_level = 0
        self.requirements = []
        self.headings = []
        self.specification = None
        self.pyname_fmt = re.compile(r"[^a-zA-Z0-9]")
        super(Visitor, self).__init__(*args, **kwargs)

    def visit_line(self, node, children):
        pass

    def process_heading(self, node, children):
        level = node[0].value.count("#")
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
        level, num = self.process_heading(node, children)
        name = node.heading_name.value
        self.headings.append(Specification.Heading(name=name, level=level, num=num))

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

        self.specification = Specification(
            name=name, description=description, author=author,
            date=date, status=status, approved_by=approved_by,
            approved_date=approved_date, approved_version=approved_version,
            version=version, group=group, type=type,
            link=link, uid=uid, parent=parent, children=children, content=None)

    def visit_requirement(self, node, children):
        level, num = self.process_heading(node, children)
        name = node.requirement_heading.requirement_name.value
        version = str(node.requirement_version.word)
        description = None
        group = None
        priority = None
        type = None
        uid = None
        link = None

        try:
            description = "\n".join([f'{"":8}{repr(line.value)}' for lines in node.requirement_description for line in lines])
            description = wstrip(description, f"{'':8}'\\n'\n")
            description = f"(\n{description}\n{'':4})"
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

        self.headings.append(Specification.Heading(name=name, level=level, num=num))
        self.requirements.append(Requirement(
            name=name, version=version, description=description,
            priority=priority, group=group, type=type,
            uid=uid, link=link, level=level, num=num))

    def visit_document(self, node, children):
        requirements = []

        for rq in self.requirements:
            pyname = re.sub(r"_+", "_", self.pyname_fmt.sub("_", rq.name))

            self.output += requirement_template.lstrip() % {
                "pyname": pyname,
                "name": repr(rq.name),
                "version": repr(rq.version),
                "description": rq.description,
                "priority": repr(rq.priority),
                "group": repr(rq.group),
                "type": repr(rq.type),
                "uid": repr(rq.uid),
                "link": repr(rq.link),
                "level": repr(rq.level),
                "num": repr(rq.num)
            }

            requirements.append(pyname)

        sep = ",\n" + "    " * 2

        self.output += specification_template.lstrip() % {
            "pyname": re.sub(r"_+", "_", self.pyname_fmt.sub("_", self.specification.name)),
            "name": repr(self.specification.name),
            "description": repr(self.specification.description),
            "author": repr(self.specification.author),
            "date": repr(self.specification.date),
            "status": repr(self.specification.status),
            "approved_by": repr(self.specification.approved_by),
            "approved_date": repr(self.specification.approved_date),
            "approved_version": repr(self.specification.approved_version),
            "version": repr(self.specification.version),
            "group": repr(self.specification.group),
            "type": repr(self.specification.type),
            "link": repr(self.specification.link),
            "uid": repr(self.specification.uid),
            "parent": repr(self.specification.parent),
            "children": repr(self.specification.children),
            "headings": f"(\n{'    ' * 2}{sep.join(f'{heading}' for heading in self.headings)}{sep})",
            "requirements": f"(\n{'    ' * 2}{sep.join(rq for rq in requirements)}{sep})",
            "content": "'''\n%s\n'''" % self.source_data.replace("'''", "\'\'\'").rstrip()
        }

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

    def inline_heading():
        return heading()

    def toc_heading():
        return _(r"#+[ \t]+"), _(r"[Tt][Aa][Bb][Ll][Ee] [Oo][Ff] [Cc][Oo][Nn][Tt][Ee][Nn][Tt][Ss]"), _(r"[ \t]*\n")

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
        return _(r"[^\n]+")

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
        return specification_heading, ZeroOrMore(inline_heading), ZeroOrMore([
            specification_author,
            specification_date,
            specification_version,
            specification_other,
            specification_approval,
            empty_line,
            _(r"[ \t]*[^\*#\n][^\n]*\n")
        ]), [toc_heading, heading]

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
