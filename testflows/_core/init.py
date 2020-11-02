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
import os
import sys
import glob
import threading

import testflows.settings as settings

from .compress import CompressedFile
from .transform.log.pipeline import RawLogPipeline
from .transform.log.pipeline import NiceLogPipeline
from .transform.log.pipeline import DotsLogPipeline
from .transform.log.pipeline import ShortLogPipeline
from .transform.log.pipeline import SlickLogPipeline
from .transform.log.pipeline import ClassicLogPipeline
from .transform.log.pipeline import FailsLogPipeline
from .templog import glob as templog_glob, parser as templog_parser, dirname as templog_dirname

def cleanup():
    """Clean up old temporary log files.
    """
    def pid_exists(pid):
        """Check if pid is alive on UNIX.

        :param pid: pid
        """
        # NOTE: pid == 0 returns True
        if pid < 0: return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            # errno.ESRCH - no such process
            return False
        except PermissionError:
            # errno.EPERM - operation not permitted (i.e., process exists)
            return True
        else:
            #  no error, we can send a signal to the process
            return True

    for file in glob.glob(os.path.join(templog_dirname(), templog_glob)):
        match = templog_parser.match(file)
        if not match:
            continue
        pid = int(match.groupdict()['pid'])
        if not pid_exists(pid):
            try:
                os.remove(file)
            except PermissionError:
                pass
            except OSError:
                raise

def stdout_raw_handler():
    """Handler to output messages to sys.stdout
    using "raw" format.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        RawLogPipeline(log, sys.stdout, tail=True).run()

def stdout_slick_handler():
    """Handler to output messages to sys.stdout
    using "slick" format.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        SlickLogPipeline(log, sys.stdout, tail=True).run()

def stdout_classic_handler():
    """Handler to output messages to sys.stdout
    using "classic" format.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        ClassicLogPipeline(log, sys.stdout, tail=True).run()

def stdout_fails_handler():
    """Handler to output messages to sys.stdout
    using "fails" format.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        FailsLogPipeline(log, sys.stdout, tail=True).run()

def stdout_new_fails_handler():
    """Handler to output messages to sys.stdout
    using "fails" format that shows only new fails.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        FailsLogPipeline(log, sys.stdout, tail=True, only_new=True).run()

def stdout_short_handler():
    """Handler to output messages to sys.stdout
    using "short" format.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        ShortLogPipeline(log, sys.stdout, tail=True).run()

def stdout_nice_handler():
    """Handler to output messages to sys.stdout
    using "nice" format.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        NiceLogPipeline(log, sys.stdout, tail=True).run()

def stdout_dots_handler():
    """Handler to output messages to sys.stdout
    using "dots" format.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        DotsLogPipeline(log, sys.stdout, tail=True).run()

def stdout_silent_handler():
    """Handler that prints no output to sys.stdout.
    """
    pass

def start_output_handler():
    output_handler_map = {
        "raw": stdout_raw_handler,
        "slick": stdout_slick_handler,
        "classic": stdout_classic_handler,
        "fails": stdout_fails_handler,
        "new-fails": stdout_new_fails_handler,
        "nice": stdout_nice_handler,
        "quiet": stdout_silent_handler,
        "short": stdout_short_handler,
        "dots": stdout_dots_handler,
    }

    handler = threading.Thread(target=output_handler_map[settings.output_format])
    handler.name = "tfs-output"
    handler.start()

def start_database_handler():
    if not settings.database:
        return

    from testflows.database import database_handler

    handler = threading.Thread(target=database_handler)
    handler.name = 'tfs-database'
    handler.start()

def init():
    """Initialization before we run the first test.
    """
    cleanup()
    start_output_handler()
    start_database_handler()
    return True
