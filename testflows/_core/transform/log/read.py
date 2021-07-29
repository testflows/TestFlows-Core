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
import time

from testflows._core.message import Message

def transform(file, tail=False, offset=False, stop=None):
    """Read lines from a file-like object.

    :param file: open file handle
    :param tail: tail mode, default: False
    :param offset: include offset with the message, default: False
    :param stop: stop event
    """
    yield None
    line = ""
    pos = 0
    stop_keyword = '{"message_keyword":"%s"' % str(Message.STOP)
    stop_keyword_len = len(stop_keyword)

    while True:
        data = file.readline()

        if type(data) is bytes:
            data = data.decode("utf-8")

        line += data

        if line.endswith("\n"):
            if stop and line[:stop_keyword_len] == stop_keyword:
                stop.set()

            if offset:
                yield (line, pos)
                pos += len(line.encode("utf-8"))
            else:
                yield line

            line = ""

        if data == "":
            if not tail:
                break
            time.sleep(0.15)
