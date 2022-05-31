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
import atexit
import signal
import threading

import testflows.settings as settings

from .compress import CompressedFile
from .transform.log.pipeline import RawLogPipeline
from .transform.log.pipeline import NiceLogPipeline
from .transform.log.pipeline import BriskLogPipeline
from .transform.log.pipeline import DotsLogPipeline
from .transform.log.pipeline import ProgressLogPipeline
from .transform.log.pipeline import ShortLogPipeline
from .transform.log.pipeline import SlickLogPipeline
from .transform.log.pipeline import ClassicLogPipeline
from .transform.log.pipeline import FailsLogPipeline
from .transform.log.pipeline import ManualLogPipeline
from .transform.log.pipeline import QuietLogPipeline
from .templog import glob as templog_glob, parser as templog_parser, dirname as templog_dirname
from .parallel import top
from .objects import Error

_handlers = []

def _at_exit():
    for handler in _handlers:
        handler.join()

atexit.register(_at_exit)

_ctrl_c = 0

def sigint_handler(signal, frame):
    global _ctrl_c
    _ctrl_c += 1

    if _ctrl_c > 1:
        raise KeyboardInterrupt()

    if top():
        top().terminate(result=Error, reason="KeyboardInterrupt")

def cleanup():
    """Clean up old temporary log files.
    """
    def pid_exists(pid):
        if pid < 0: return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        else:
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
        SlickLogPipeline(log, sys.stdout, tail=True, show_input=False).run()

def stdout_classic_handler():
    """Handler to output messages to sys.stdout
    using "classic" format.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        ClassicLogPipeline(log, sys.stdout, tail=True, show_input=False).run()

def stdout_fails_handler():
    """Handler to output messages to sys.stdout
    using "fails" format.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        FailsLogPipeline(log, sys.stdout, tail=True, show_input=False).run()

def stdout_new_fails_handler():
    """Handler to output messages to sys.stdout
    using "fails" format that shows only new fails.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        FailsLogPipeline(log, sys.stdout, tail=True, only_new=True, show_input=False).run()

def stdout_short_handler():
    """Handler to output messages to sys.stdout
    using "short" format.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        ShortLogPipeline(log, sys.stdout, tail=True, show_input=False).run()

def stdout_nice_handler():
    """Handler to output messages to sys.stdout
    using "nice" format.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        NiceLogPipeline(log, sys.stdout, tail=True, show_input=False).run()

def stdout_brisk_handler():
    """Handler to output messages to sys.stdout
    using "brisk" format.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        BriskLogPipeline(log, sys.stdout, tail=True, show_input=False).run()

def stdout_manual_handler():
    """Handler to output messages to sys.stdout
    using "manual" format.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        ManualLogPipeline(log, sys.stdout, tail=True, show_input=False).run()

def stdout_dots_handler():
    """Handler to output messages to sys.stdout
    using "dots" format.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        DotsLogPipeline(log, sys.stdout, tail=True, show_input=False).run()

def stdout_progress_handler():
    """Handler to output messages to sys.stdout
    using "progress" format.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        ProgressLogPipeline(log, sys.stdout, tail=True, show_input=False).run()

def stdout_quiet_handler():
    """Handler that prints no output to sys.stdout unless
    top level test fails.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        QuietLogPipeline(log, sys.stdout, tail=True, show_input=False).run()

def start_output_handler():
    output_handler_map = {
        "raw": stdout_raw_handler,
        "slick": stdout_slick_handler,
        "classic": stdout_classic_handler,
        "manual": stdout_manual_handler,
        "fails": stdout_fails_handler,
        "new-fails": stdout_new_fails_handler,
        "nice": stdout_nice_handler,
        "brisk": stdout_brisk_handler,
        "quiet": stdout_quiet_handler,
        "short": stdout_short_handler,
        "dots": stdout_dots_handler,
        "progress": stdout_progress_handler,
    }

    handler = threading.Thread(target=output_handler_map[settings.output_format])
    handler.name = "tfs-output"
    handler.start()
    _handlers.append(handler)

def start_database_handler():
    if not settings.database:
        return

    from testflows.database import database_handler

    handler = threading.Thread(target=database_handler)
    handler.name = 'tfs-database'
    handler.start()
    _handlers.append(handler)

def init():
    """Initialization before we run the first test.
    """
    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError("top level test was not started in main thread")
    signal.signal(signal.SIGINT, sigint_handler)
    cleanup()
    start_output_handler()
    start_database_handler()
    return True
