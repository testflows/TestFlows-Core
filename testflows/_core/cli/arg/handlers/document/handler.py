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
from testflows._core.cli.arg.common import epilog
from testflows._core.cli.arg.common import HelpFormatter
from testflows._core.cli.arg.handlers.handler import Handler as HandlerBase
from testflows._core.cli.arg.handlers.document.convert import Handler as convert_handler
from testflows._core.cli.arg.handlers.document.toc import Handler as toc_handler
from testflows._core.cli.arg.handlers.document.new.handler import Handler as new_handler

class Handler(HandlerBase):
    @classmethod
    def add_command(cls, commands):
        parser = commands.add_parser("document", help="document processing", epilog=epilog(),
            description="Work with a document.",
            formatter_class=HelpFormatter)

        document_commands = parser.add_subparsers(title="commands", metavar="command",
            description=None, help=None)
        document_commands.required = True
        convert_handler.add_command(document_commands)
        toc_handler.add_command(document_commands)
        new_handler.add_command(document_commands)
        try:
            from testflows.texts.run import Handler as run_handler
            run_handler.add_command(document_commands)
        except ImportError:
            pass
