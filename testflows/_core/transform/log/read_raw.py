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
def transform(file, offset=False, stop=None, bufsize=10485760, encoding=None):
    """Raw read from a file-like object.

    :param file: open file handle
    :param offset: include offset with the message, default: False
    :param stop: stop event
    """
    yield None
    pos = 0

    while True:
        data = file.read(bufsize)
        if encoding and type(data) is bytes:
            data = data.decode(encoding)
        if data:
            if offset:
                yield (data, pos)
                if encoding:
                    pos += len(data.encode(encoding))
                else:
                    pos += len(data)
            else:
                yield data
        if data == "" if encoding else data == b"":
            if stop:
                stop.set()
            yield None
            break
