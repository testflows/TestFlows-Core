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
import subprocess

from testflows._core.message import Message

def transform(file, command, tail=False, stop=None):
    """Read lines from a file-like object and
    filter them using Unix grep utility.

    :param file: open file handle
    :param command: filter command (like grep)
    :param tail: tail mode, default: False
    :param stop: stop event
    """
    yield None

    stop_keyword = ('{"message_keyword":"%s"' % str(Message.STOP)).encode("utf-8")
    stop_keyword_len = len(stop_keyword)

    process = subprocess.Popen(f"tfs transform raw | {command}", stdin=file, stdout=subprocess.PIPE, shell=True)

    while True:
        line = process.stdout.readline()

        if line == b"":
            if not tail:
                break

            if process.poll() is not None:
                break

            continue

        if stop and line[:stop_keyword_len] == stop_keyword:
            stop.set()

        yield line.decode("utf-8")

        if stop and stop.is_set():
            break

    if stop:
        stop.set()

    yield None
