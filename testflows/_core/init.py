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
from .transform.log.pipeline import ParallelNiceLogPipeline
from .transform.log.pipeline import BriskLogPipeline
from .transform.log.pipeline import PlainLogPipeline
from .transform.log.pipeline import DotsLogPipeline
from .transform.log.pipeline import ProgressLogPipeline
from .transform.log.pipeline import ShortLogPipeline
from .transform.log.pipeline import SlickLogPipeline
from .transform.log.pipeline import ClassicLogPipeline
from .transform.log.pipeline import FailsLogPipeline
from .transform.log.pipeline import ManualLogPipeline
from .transform.log.pipeline import QuietLogPipeline
from .temp import glob as temp_glob, parser as temp_parser, dirname as temp_dirname
from .parallel import top
from .objects import Error
from .jupyter_notebook import is_jupyter_notebook

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
    """Clean up old temporary log files."""

    def pid_exists(pid):
        if pid < 0:
            return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        else:
            return True

    for file in glob.glob(os.path.join(temp_dirname(), temp_glob)):
        match = temp_parser(extension="*").match(file)
        if not match:
            continue
        pid = int(match.groupdict()["pid"])
        if not pid_exists(pid):
            try:
                os.remove(file)
            except FileNotFoundError:
                pass
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
        FailsLogPipeline(
            log, sys.stdout, tail=True, only_new=True, show_input=False
        ).run()


def stdout_brisk_fails_handler():
    """Handler to output messages to sys.stdout
    using "fails" format with brisk dump.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        FailsLogPipeline(log, sys.stdout, tail=True, brisk=True, show_input=False).run()


def stdout_brisk_new_fails_handler():
    """Handler to output messages to sys.stdout
    using "fails" format that shows only new fails with brisk dump.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        FailsLogPipeline(
            log, sys.stdout, tail=True, brisk=True, only_new=True, show_input=False
        ).run()


def stdout_plain_fails_handler():
    """Handler to output messages to sys.stdout
    using "fails" format with plain dump.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        FailsLogPipeline(log, sys.stdout, tail=True, plain=True, show_input=False).run()


def stdout_plain_new_fails_handler():
    """Handler to output messages to sys.stdout
    using "fails" format that shows only new fails with plain dump.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        FailsLogPipeline(
            log, sys.stdout, tail=True, plain=True, only_new=True, show_input=False
        ).run()


def stdout_nice_fails_handler():
    """Handler to output messages to sys.stdout
    using "fails" format with nice dump.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        FailsLogPipeline(log, sys.stdout, tail=True, nice=True, show_input=False).run()


def stdout_nice_new_fails_handler():
    """Handler to output messages to sys.stdout
    using "fails" format that shows only new fails with nice dump.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        FailsLogPipeline(
            log, sys.stdout, tail=True, nice=True, only_new=True, show_input=False
        ).run()


def stdout_pnice_fails_handler():
    """Handler to output messages to sys.stdout
    using "fails" format with parallel nice dump.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        FailsLogPipeline(log, sys.stdout, tail=True, pnice=True, show_input=False).run()


def stdout_pnice_new_fails_handler():
    """Handler to output messages to sys.stdout
    using "fails" format that shows only new fails with parallel nice dump.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        FailsLogPipeline(
            log, sys.stdout, tail=True, pnice=True, only_new=True, show_input=False
        ).run()


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


def stdout_pnice_handler():
    """Handler to output messages to sys.stdout
    using "pnice" format.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        ParallelNiceLogPipeline(log, sys.stdout, tail=True, show_input=False).run()


def stdout_brisk_handler():
    """Handler to output messages to sys.stdout
    using "brisk" format.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        BriskLogPipeline(log, sys.stdout, tail=True, show_input=False).run()


def stdout_plain_handler():
    """Handler to output messages to sys.stdout
    using "plain" format.
    """
    with CompressedFile(settings.read_logfile, tail=True) as log:
        log.seek(0)
        PlainLogPipeline(log, sys.stdout, tail=True, show_input=False).run()


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
        "brisk-fails": stdout_brisk_fails_handler,
        "brisk-new-fails": stdout_brisk_new_fails_handler,
        "plain-fails": stdout_plain_fails_handler,
        "plain-new-fails": stdout_plain_new_fails_handler,
        "nice-fails": stdout_nice_fails_handler,
        "nice-new-fails": stdout_nice_new_fails_handler,
        "pnice-fails": stdout_pnice_fails_handler,
        "pnice-new-fails": stdout_pnice_new_fails_handler,
        "nice": stdout_nice_handler,
        "pnice": stdout_pnice_handler,
        "brisk": stdout_brisk_handler,
        "plain": stdout_plain_handler,
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
    handler.name = "tfs-database"
    handler.start()
    _handlers.append(handler)


def init():
    """Initialization before we run the first test."""
    if not is_jupyter_notebook():
        if threading.current_thread() is not threading.main_thread():
            raise RuntimeError("top level test was not started in main thread")
        signal.signal(signal.SIGINT, sigint_handler)
    cleanup()
    start_output_handler()
    start_database_handler()
    return True
