# Copyright 2020 Katteli Inc.
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

from testflows._core.flags import Flags, SKIP
from testflows._core.message import Message

def format_metric(msg, metrics):
    metrics.append(msg)

formatters = {
    Message.METRIC.name: (format_metric,),
}

def transform(metrics):
    """Transform parsed log into metrics.
    """
    line = None
    while True:
        if line is not None:
            msg = line
            formatter = formatters.get(line["message_keyword"], None)
            if formatter:
                flags = Flags(line["test_flags"])
                if flags & SKIP and settings.show_skipped is False:
                    line = None
                else:
                    line = formatter[0](line, *formatter[1:], metrics)
            else:
                line = None
        line = yield line