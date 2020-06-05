# Copyright 2019 Katteli Inc.
# TestFlows Test Framework (http://testflows.com)
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
import testflows.settings as settings

from testflows._core.constants import id_sep
from testflows._core.message import Message, loads

def transform(stop=None):
    """Transform log line into parsed list.

    :param stop: stop event, default: None
    """
    msg = None
    m = None
    stop_id = None

    while True:
        if msg is not None:
            try:
                m = loads(msg)
                if stop_id is None:
                    stop_id = m["test_id"]
                if m["message_keyword"] == Message.RESULT:
                    if stop and m["test_id"] == stop_id:
                        stop.set()
            except (IndexError, Exception):
                yield None
                continue
        msg = yield m
