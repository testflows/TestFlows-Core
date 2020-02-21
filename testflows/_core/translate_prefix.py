import re

from testflows._core.contrib.arpeggio import *
from testflows._core.contrib.arpeggio import RegExMatch as _

class DebugVisitor(PTNodeVisitor):
    def visit__default__(self, node, children):
        print(node.name, node)
        return super(Visitor, self).visit__default__(node, children)

class RegexBuilder(PTNodeVisitor):
    def __init__(self, *args, **kwargs):
        self.stacks = [[r'']]
        self.process_subpattern = [True]
        self.repeated_group_start_idx = []
        self.repeated_as_many_group_start_idx = []
        self.not_followed_by_group_start_idx = []
        super(RegexBuilder, self).__init__(*args, **kwargs)

    def visit_char(self, node, children):
        self.stacks[-1][-1] += re.escape(node.value[-1])

    def visit_separator(self, node, children):
        self.stacks[-1].append('/')

    def visit_wildcard(self, node, children):
        self.stacks[-1].append(r'.*')

    def visit_wildcard_without_separator(self, node, children):
        self.stacks[-1].append(r'[^/]+')

    def visit_any_char(self, node, children):
        self.stacks[-1].append(r'.')

    def visit_any_char_in_seq(self, node, children):
        chars = node.value[1:-1]
        chars = re.sub(r"\\(.)", r"\1", chars)
        regex = f'[{"".join([re.escape(c) for c in chars])}]'
        if '/' in chars:
            self.stacks[-1].append(regex)
        else:
            self.stacks[-1][-1] += regex

    def visit_any_char_not_in_seq(self, node, children):
        chars = node.value[2:-1]
        chars = re.sub(r"\\(.)", r"\1", chars)
        regex = f'[^{"".join([re.escape(c) for c in chars])}]'
        if '/' in chars:
            self.stacks[-1].append(regex)
        else:
            self.stacks[-1][-1] += regex

    def process_stack(self, stack, process):
        def regex():
            if not stack:
                return ''
            item = stack.pop(0)
            if process == "optional" and stack:
                must_be_followed_by = ['$']
                for i in range(len(stack)):
                    must_be_followed_by.append('(' + ''.join(stack[:i+1]) + ')')
                return f'({item}(?={"|".join(must_be_followed_by)}){regex()})?'
            else:
                return f'({item}{regex()})?'
        return regex()

    def visit_subpattern(self, node, children):
        process = self.process_subpattern.pop()
        if not process:
            return
        stack = self.stacks.pop()
        return self.process_stack(stack, process)

    def visit_group_start(self, node, children):
        self.process_subpattern.append(False)

    def visit_group(self, node, children):
        pass

    def visit_not_followed_by_group_start(self, node, children):
        self.process_subpattern.append(False)
        self.stacks[-1].append('')
        self.not_followed_by_group_start_idx.append(len(self.stacks[-1])-1)

    def visit_not_followed_by_group(self, node, children):
        idx = self.not_followed_by_group_start_idx.pop()
        items = self.stacks[-1][idx:]
        self.stacks[-1] = self.stacks[-1][:idx] + [f"(?!{''.join(items)})"]

    def visit_repeated_group_start(self, node, children):
        self.process_subpattern.append(False)
        self.repeated_group_start_idx.append(len(self.stacks[-1]))

    def visit_repeated_group(self, node, children):
        repeat = int(node[2].value[-2])
        idx = self.repeated_group_start_idx.pop()
        self.stacks[-1] = self.stacks[-1][:idx] + self.stacks[-1][idx:] * repeat

    def visit_repeated_as_many_group_start(self, node, children):
        self.process_subpattern.append(False)
        self.repeated_as_many_group_start_idx.append(len(self.stacks[-1]))

    def visit_repeated_as_many_group(self, node, children):
        m, n = node[2].value[2:-1].split(',')
        m, n = int(m), int(n)
        idx = self.repeated_as_many_group_start_idx.pop()
        items = self.stacks[-1][idx:]
        optional = [self.process_stack(list(items), "optional")]
        self.stacks[-1] = self.stacks[-1][:idx] + items * m + optional * (n - m)

    def visit_optional_group_start(self, node, children):
        self.process_subpattern.append("optional")
        self.stacks.append([r''])

    def visit_optional_group(self, node, children):
        self.stacks[-1].append(f'({children[0]})?')

    def visit_pattern(self, node, children):
        return r'(?s:%s)\Z' % children[0]

def Parser():
    def char():
        return RegExMatch(r"(\\.)|[^/!\*\:\?\(\)\[\]\{\}]")

    def wildcard():
        return RegExMatch(r"[*]")

    def wildcard_without_separator():
        return RegExMatch(r"[:]")

    def any_char():
        return RegExMatch(r"[\?]")

    def any_char_in_seq():
        return RegExMatch(r"\[(([^!\*\:\?\)\(\]\[\{\}])|(\\.))*\]")

    def any_char_not_in_seq():
        return RegExMatch(r"\[\!(([^!\*\:\?\)\(\]\[\{\}])|(\\.))*\]")

    def separator():
        return RegExMatch(r"/")

    def group_start():
        return '('

    def optional_group_start():
        return '('

    def repeated_group_start():
        return '('

    def repeated_as_many_group_start():
        return '('

    def not_followed_by_group_start():
        return '(?!'

    def group():
        return group_start, ZeroOrMore(subpattern), ')'

    def not_followed_by_group():
        return not_followed_by_group_start, ZeroOrMore(subpattern), ')'

    def optional_group():
        return optional_group_start, ZeroOrMore(subpattern), RegExMatch(r'\)\?')

    def repeated_group():
        return repeated_group_start, ZeroOrMore(subpattern), RegExMatch(r'\)\{\d+\}')

    def repeated_as_many_group():
        return repeated_as_many_group_start, ZeroOrMore(subpattern), RegExMatch(r'\)\{\d+,\d+\}')

    def subpattern():
        return OneOrMore([not_followed_by_group, optional_group, repeated_group, repeated_as_many_group, group, char, separator, any_char_not_in_seq, any_char_in_seq, any_char, wildcard, wildcard_without_separator])

    def pattern():
        return subpattern, EOF

    return ParserPython(pattern, memoization=True)

parser = Parser()

def translate(expr, debug=False):
    tree = parser.parse(expr)
    regex = visit_parse_tree(tree, RegexBuilder())
    if debug:
        print(f"expr: {expr}")
        print(f"regex: {regex}")
    return regex
