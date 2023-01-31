# Copyright 2023 Katteli Inc.
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
import time
import signal
import threading
import subprocess

import testflows._core.cli.arg.type as argtype

from testflows._core.cli.arg.common import epilog
from testflows._core.cli.arg.common import HelpFormatter
from testflows._core.cli.arg.handlers.handler import Handler as HandlerBase

description = """Run test program.

If either '--stdout' or '--stderr' is specified then '--no-colors'
is automatically applied to the test program.
You can overwrite this behavior by passing `--no-colors off` option
to the test program.

Examples:

Write pid, stdout and stderr to files.
    tfs run --pid run.pid --stdout run.out --stderr run.err test.py -- -o classic

Write pid, stdout and stderr to files but silence output to the terminal.
    tfs run --no-output --pid run.pid --stdout run.out --stderr run.err test.py -- -o classic

Redirect stdout to file but turn colors back on.
    tfs run --stdout run.out --stderr run.err test.py -- -o classic --no-colors off

Write exitcode to file
    tfs run --exitcode run.exitcode test.py
"""


class Handler(HandlerBase):
    @classmethod
    def add_command(cls, commands):
        parser = commands.add_parser(
            "run",
            help="run test program",
            epilog=epilog(),
            description=description,
            formatter_class=HelpFormatter,
        )

        parser.add_argument("--pid", metavar="file", type=str, help="pid file")
        parser.add_argument(
            "--exitcode", metavar="file", type=str, help="exit code file"
        )

        parser.add_argument(
            "--stdout", metavar="file", type=str, help="file where to redirect stdout"
        )

        parser.add_argument(
            "--stderr", metavar="file", type=str, help="file where to redirect stderr"
        )

        parser.add_argument(
            "-q",
            "--no-output",
            action="store_true",
            default=False,
            help="disable output to the terminal from redirected stdout",
        )

        parser.add_argument(
            "program", metavar="program", type=argtype.path, help="test program to run"
        )

        parser.add_argument(
            "args", metavar="args", nargs="*", type=str, help="test program arguments"
        )

        parser.set_defaults(func=cls())

    def _reader(self, filename, out, process, flush=True, timeout=0.1):
        """Read contents of file and write to the specified output."""
        with open(filename, "r") as fd:
            while True:
                try:
                    out.write(fd.read())
                    if flush:
                        out.flush()
                finally:
                    if process.returncode is not None:
                        break
                    time.sleep(timeout)

    def handle(self, args):
        command = ["python3", os.path.abspath(args.program)]

        stdout = sys.stdout
        if args.stdout:
            stdout = open(args.stdout, "w")

        stderr = sys.stderr
        if args.stderr:
            stderr = open(args.stderr, "w")

        if args.stdout or args.stderr:
            command.append("--no-colors")

        command += args.args

        process = subprocess.Popen(
            command, stdin=None, stderr=stderr, stdout=stdout, close_fds=True
        )

        if args.pid:
            with open(args.pid, "w") as fd:
                fd.write(f"{os.getpid()}\n")

        stop_event = threading.Event()
        stdout_reader = None
        stderr_reader = None

        try:
            if not args.no_output:
                if args.stdout:
                    stdout_reader = threading.Thread(
                        target=self._reader,
                        args=(args.stdout, sys.stdout, process, True),
                    )
                    stdout_reader.start()
            if args.stderr:
                stderr_reader = threading.Thread(
                    target=self._reader, args=(args.stderr, sys.stderr, process)
                )
                stderr_reader.start()

            while True:
                try:
                    if process.poll() is not None:
                        break
                    if (
                        subprocess.call(
                            ["kill", "-0", f"{process.pid}"],
                            stderr=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL,
                        )
                        != 0
                    ):
                        break
                    time.sleep(0.25)
                except KeyboardInterrupt:
                    process.send_signal(signal.SIGINT)
                except BaseException:
                    process.terminate()
        finally:
            try:
                if stdout_reader is not None:
                    stdout_reader.join()
                if stderr_reader is not None:
                    stderr_reader.join()
            finally:
                sys.stdout.flush()
                sys.stderr.flush()
                if args.exitcode:
                    with open(args.exitcode, "w") as fd:
                        fd.write(f"{process.returncode}\n")
                sys.exit(process.returncode if process.returncode is not None else -1)
