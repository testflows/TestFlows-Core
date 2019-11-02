# Copyright 2019 Vitaliy Zakaznikov (TestFlows Test Framework http://testflows.com)
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
def transform(file, tail=False, offset=False):
    """Read lines from a file-like object.

    :param file: open file handle
    :param tail: tail mode, default: False
    :param offset: include offset with the message, default: False
    """
    yield None
    line = ""
    pos = 0
    while True:
        line += file.readline()
        if line.endswith("\n"):
            if offset:
                yield (line, pos)
                pos += len(line.encode("utf-8"))
            else:
                yield line
            line = ""
