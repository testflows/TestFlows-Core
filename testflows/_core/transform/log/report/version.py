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

from testflows._core.cli.colors import color
from testflows._core.utils.timefuncs import localfromtimestamp
from testflows._core.message import Message

def transform(stop, divider="\n"):
    """Transform parsed log line into a nice format.

    :param stop: stop event
    """
    line = None
    version = None
    started = None
    while True:
        if line is not None:
            if line["message_keyword"] == Message.VERSION.name:
                version = line["framework_version"]
                started = localfromtimestamp(line["message_time"])
            line = None

        if stop.is_set():
            if started is not None and version is not None:
                line = color(f"{divider}Executed on {started:%b %d,%Y %-H:%M}\nTestFlows.com Open-Source Software Testing Framework v{version}",
                    "white", attrs=["dim"]) + "\n"

        line = yield line
