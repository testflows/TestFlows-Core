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
from testflows._core.contrib.pygments.lexer import RegexLexer, bygroups
from testflows._core.contrib.pygments.token import *

__all__ = ['TestFlowsLexer']

class TestFlowsLexer(RegexLexer):
    name = 'TestFlows'
    aliases = ['tfs']
    filenames = ['*.tfs']

    tokens = {
        'root': [
            (r'(\s*)(Module|Suite|Feature|Test|Scenario|Example|Outline)( .*)', bygroups(Keyword, Keyword.Namespace, Name.Namespace)),
            (r'(\s*)(Step|Background|Given|When|Then|But|And|By|Finally)', Keyword),
            (r'(\s*)(Arguments|Requirements|Attributes|Tags|Examples)', Name.Label),
            (r'(\s*)OK', Result.OK),
            (r'(\s*)Fail', Result.Fail),
            (r'(\s*)Skip', Result.Skip),
            (r'(\s*)Error', Result.Error),
            (r'(\s*)Null', Result.Null),
            (r'(\s*)(XOK|XFail|XNull|XError)', Result.Xout),
            (r' .*\n', Text),
        ]
    }
