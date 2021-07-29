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
import testflows.settings as settings

from testflows._core.constants import id_sep
from testflows._core.message import Message, loads

def transform():
    """Transform log line by parsing it.
    """
    msg = None
    parsed_msg = None

    while True:
        if msg is not None:
            try:
                parsed_msg = loads(msg)
            except (IndexError, Exception):
                yield None
                continue
        else:
            parsed_msg = None

        msg = yield parsed_msg
