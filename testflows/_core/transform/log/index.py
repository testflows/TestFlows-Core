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
import json

import testflows.settings as settings

from testflows._core.message import MessageMap
from testflows._core.transform.log import message

def transform(stop=None):
    """Transform log line into an index file entry.

    :param stop: stop event, default: None
    """
    prefix = message.RawFormat.prefix
    message_map = message.message_map

    msg = None
    while True:
        if msg is not None:
            try:
                fields = json.loads(f"[{msg}]")
                keyword = fields[prefix.keyword]
                if issubclass(message_map[keyword], message.RawTest):
                    test = message_map[keyword](*fields)
                    msg = f"\"{test.name}\",{test.p_id}\n"
                else:
                    msg = None
            except (IndexError, Exception):
                raise Exception(f"invalid message: {msg}\n")
        msg = yield msg
