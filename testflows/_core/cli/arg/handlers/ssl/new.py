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
import sys
from testflows._core.cli.text import secondary
from testflows._core.cli.arg.common import epilog
from testflows._core.cli.arg.common import HelpFormatter
from testflows._core.cli.arg.handlers.handler import Handler as HandlerBase
from testflows._core.parallel.ssl import (
    new_ca_cert,
    new_host_cert,
    default_ssl_dir,
    get_ca_cert,
)


class Handler(HandlerBase):
    @classmethod
    def add_command(cls, commands):
        parser = commands.add_parser(
            "new",
            help="new configuration",
            epilog=epilog(),
            description=(
                "Generate new SSL configuration by creating new certificate authority (CA) and host\n"
                "private keys and certificates.\n\nBy default, create both new CA and host keys and certificates."
            ),
            formatter_class=HelpFormatter,
        )

        parser.add_argument(
            "--ca",
            action="store_true",
            help="create new certificate authority (CA) key and certificate",
            default=False,
        )

        parser.add_argument(
            "--host",
            action="store_true",
            help="create new host key and certificate",
            default=False,
        )

        parser.set_defaults(func=cls())

    def handle(self, args):
        ssl_dir = default_ssl_dir()

        os.makedirs(ssl_dir, exist_ok=True)

        if not args.ca and not args.host:
            args.ca = True
            args.host = True

        if args.ca:
            ca_cert = new_ca_cert(dir=ssl_dir, verbose=False)
            print(secondary(f"CA key: {ca_cert.key}", eol=""))
            print(secondary(f"CA certificate: {ca_cert.cert}", eol=""))
        else:
            ca_cert = get_ca_cert(dir=ssl_dir)

        if args.host:
            host_cert = new_host_cert(dir=ssl_dir, ca_cert=ca_cert, verbose=False)
            print(secondary(f"Host key: {host_cert.key}", eol=""))
            print(secondary(f"Host certificate: {host_cert.cert}", eol=""))
