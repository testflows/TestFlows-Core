# Copyright 2024 Katteli Inc.
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
import os
import textwrap
from testflows._core.cli.text import primary, secondary
from testflows._core.cli.arg.common import epilog
from testflows._core.cli.arg.common import HelpFormatter
from testflows._core.cli.arg.handlers.handler import Handler as HandlerBase
from testflows._core.parallel.ssl import show_key, show_cert


class Handler(HandlerBase):
    @classmethod
    def add_command(cls, commands):
        parser = commands.add_parser(
            "show",
            help="show configuration",
            epilog=epilog(),
            description=(
                "Show SSL configuration by dumping certificate authority (CA) and host\n"
                "private keys and certificates.\n\nBy default, show both CA and host keys and certificates."
            ),
            formatter_class=HelpFormatter,
        )

        parser.add_argument(
            "--ca",
            action="store_true",
            help="show certificate authority (CA) key and certificate",
            default=False,
        )

        parser.add_argument(
            "--ca-key",
            action="store_true",
            help="show certificate authority (CA) key",
            default=False,
        )

        parser.add_argument(
            "--ca-cert",
            action="store_true",
            help="show certificate authority (CA) certificate",
            default=False,
        )

        parser.add_argument(
            "--host",
            action="store_true",
            help="show host key and certificate",
            default=False,
        )

        parser.add_argument(
            "--host-key",
            action="store_true",
            help="show host key",
            default=False,
        )

        parser.add_argument(
            "--host-cert",
            action="store_true",
            help="show host certificate",
            default=False,
        )

        parser.set_defaults(func=cls())

    def handle(self, args):
        ssl_dir = os.path.expanduser("~/.testflows/ssl")
        os.makedirs(ssl_dir, exist_ok=True)

        if (
            not args.ca
            and not args.ca_key
            and not args.ca_cert
            and not args.host
            and not args.host_key
            and not args.host_cert
        ):
            args.ca = True
            args.host = True

        if args.ca:
            args.ca_key = True
            args.ca_cert = True

        if args.ca_key:
            print(primary("Certificate Authority (CA) key", eol=""))
            ca_key_output = show_key(dir=ssl_dir, key="ca.key")
            print(
                secondary(textwrap.indent(ca_key_output.strip(), prefix="  "), eol="")
            )

        if args.ca_cert:
            print(primary("Certificate Authority (CA) certificate", eol=""))
            ca_crt_output = show_cert(dir=ssl_dir, cert="ca.crt")
            print(
                secondary(textwrap.indent(ca_crt_output.strip(), prefix="  "), eol="")
            )

        if args.host:
            args.host_key = True
            args.host_cert = True

        if args.host_key:
            print(primary("Host key", eol=""))
            host_key_output = show_key(dir=ssl_dir, key="host.key")
            print(
                secondary(textwrap.indent(host_key_output.strip(), prefix="  "), eol="")
            )

        if args.host_cert:
            print(primary("Host certificate", eol=""))
            host_crt_output = show_cert(dir=ssl_dir, cert="host.crt")
            print(
                secondary(textwrap.indent(host_crt_output.strip(), prefix="  "), eol="")
            )
