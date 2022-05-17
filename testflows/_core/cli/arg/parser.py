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

from argparse import ArgumentParser as ArgumentParserBase

from .common import epilog
from .common import description
from .common import HelpFormatter
from .handlers.transform.handler import Handler as transform_handler
from .handlers.document.handler import Handler as document_handler
from .handlers.requirement.handler import Handler as requirement_handler
from .handlers.report.handler import Handler as report_handler
from .handlers.show.handler import Handler as show_handler
from .handlers.log import Handler as log_handler
from .type import onoff as onoff_type

try:
    from testflows.database.cli.handler import Handler as database_handler
except:
    database_handler = None

try:
    from testflows.enterprise._core.cli.handler import Handler as enterprise_handler
except:
    enterprise_handler = None

from testflows._core import __version__, __license__

class ArgumentParser(ArgumentParserBase):
    """Customized argument parser.
    """
    def __init__(self, *args, **kwargs):
        description_prog = kwargs.pop("description_prog", None)
        kwargs["epilog"] = kwargs.pop("epilog", epilog())
        kwargs["description"] = description(textwrap.dedent(kwargs.pop("description", None) or ""), prog=description_prog)
        kwargs["formatter_class"] = kwargs.pop("formatter_class", HelpFormatter)
        return super(ArgumentParser, self).__init__(*args, **kwargs)

parser = ArgumentParser(prog="tfs")

parser.add_argument("--debug", dest="debug", action="store_true",
                    help="enable debugging mode", default=False)
parser.add_argument("--no-colors", dest="no_colors", action="store_true",
                    help="disable terminal color highlighting", default=False)
parser.add_argument("--show-skipped", dest="show_skipped", action="store_true",
                    help="show skipped tests, default: False", default=False)
parser.add_argument("--trim-results", dest="trim_results", type=onoff_type,
                    help="enable or disable trimming of result messages, default: on",
                    metavar=onoff_type.metavar, default="on")
parser.add_argument("-v", "--version", action="version", version=f"{__version__}")
parser.add_argument("--license", action="version", help="show program's license and exit", version=f"{__license__}")

commands = parser.add_subparsers(title='commands', metavar='command', description=None, help=None)

log_handler.add_command(commands)
report_handler.add_command(commands)
transform_handler.add_command(commands)
requirement_handler.add_command(commands)
document_handler.add_command(commands)
show_handler.add_command(commands)

if database_handler:
    database_handler.add_command(commands)

if enterprise_handler:
    enterprise_handler.add_command(commands)