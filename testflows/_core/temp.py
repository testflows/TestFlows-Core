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
import os
import re
import time
import tempfile

parser = re.compile(r".*testflows\.(?P<ppid>\d+)\.(?P<ts>\d+)\.(?P<tss>\d+)\.(?P<pid>\d+)\.log")
glob = "testflows.*.log"


def ppid_glob(ppid):
    return f"testflows.{ppid}.*.log"

def dirname():
    """Return temporary log file directory name.
    """
    return tempfile.gettempdir()

def filename():
    """Return temporary log file name.
    """
    return os.path.join(tempfile.gettempdir(), f"testflows.{os.getppid()}.{time.time():017.7f}.{os.getpid()}.log")
