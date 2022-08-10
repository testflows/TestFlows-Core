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
import time
import random
import inspect
import builtins
import functools
import threading
import importlib

from collections import namedtuple

import testflows.settings as settings
import testflows._core.tracing as tracing
import testflows._core.contrib.yaml as yaml
import testflows._core.contrib.schema as schema

from .parallel.asyncio import asyncio
from .templog import filename as templog_filename
from .exceptions import DummyTestException, ResultException, TestIteration, DescriptionError, TestRerunIndividually
from .exceptions import TerminatedError
from .flags import Flags, SKIP, TE, FAIL_NOT_COUNTED, ERROR_NOT_COUNTED, NULL_NOT_COUNTED, MANDATORY, MANUAL, AUTO
from .flags import REMOTE, PARALLEL, NO_PARALLEL, ASYNC, REPEATED, NOT_REPEATABLE, RETRIED, RETRY, NESTED_RETRY, LAST_RETRY
from .flags import XOK, XFAIL, XNULL, XERROR, XRESULT
from .flags import EOK, EFAIL, EERROR, ESKIP, ERESULT
from .flags import CFLAGS, PAUSE_BEFORE, PAUSE_AFTER, PAUSE_ON_PASS, PAUSE_ON_FAIL
from .flags import SETUP, CLEANUP
from .testtype import TestType, TestSubType
from .objects import get, Null, OK, Fail, Skip, Error, PassResults, FailResults, NonFailResults
from .objects import Argument, Attribute, Requirement, ArgumentParser
from .objects import ExamplesTable, Specification
from .objects import NamedValue, OnlyTags, SkipTags
from .objects import RSASecret, Secrets
from .constants import name_sep, id_sep
from .io import TestIO
from .name import join, depth, match, absname, isabs
from .funcs import exception, pause, result, value, input
from .init import init
from .cli.arg.parser import ArgumentParser as ArgumentParserClass
from .cli.arg.common import epilog as common_epilog
from .cli.arg.exit import ExitWithError, ExitException
from .cli.arg.type import key_value as key_value_type, repeat as repeat_type
from .cli.arg.type import tags_filter as tags_filter_type, retry as retry_type
from .cli.arg.type import logfile as logfile_type, rsa_private_key_pem_file as rsa_private_key_pem_file_type
from .cli.arg.type import file as file_type
from .cli.arg.type import onoff as onoff_type, NoneValue, count as count_type, trace_level as trace_level_type
from .cli.text import danger, warning
from .exceptions import exception as get_exception
from .filters import The
from .utils.sort import human as human_sort
from .transform.log.pipeline import ResultsLogPipeline
from .parallel import current, top, previous, _check_parallel_context, join as parallel_join
from .parallel import convert_result_to_concurrent_future
from .parallel.executor.thread import ThreadPoolExecutor, GlobalThreadPoolExecutor
from .parallel.executor.asyncio import AsyncPoolExecutor, GlobalAsyncPoolExecutor
from .parallel.executor.process import ProcessPoolExecutor, GlobalProcessPoolExecutor
from .parallel.asyncio import is_running_in_event_loop, async_next, wrap_future, OptionalFuture

tracer = tracing.getLogger(__name__)

try:
    import testflows.database as database_module
except:
    database_module = None

output_formats = ["new-fails", "fails", "classic", "slick", "nice",
    "brisk", "quiet", "short", "manual", "dots", "progress", "raw"]

rerun_results = ["fails", "passes", "xouts", "ok", "fail", "error", "null",
    "xok", "xfail", "xerror", "xnull", "skip"]

# global secrets registry
settings.secrets_registry = Secrets()

async def run_async_generator(generator, consume=False):
    """Run async generator.
    """
    if consume:
        async for item in generator:
            pass
        return
    return await async_next(generator)

def run_generator(generator, consume=False):
    """Run generator.
    """
    if consume:
        for item in generator:
            pass
        return
    return next(generator)

def dummy(*args, **kwargs):
    pass

class DummyTest(object):
    """Base class for dummy tests.
    """
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        def dummy(*args, **kwargs):
            pass

        self.trace = sys.gettrace()
        sys.settrace(self.__skip__)

    def __skip__(self, *args):
        sys.settrace(self.trace)
        raise DummyTestException()

    def __exit__(self, exception_type, exception_value, exception_traceback):
        if isinstance(exception_value, DummyTestException):
            return True

class Context(object):
    """Test context.
    """
    def __init__(self, parent, state=None):
        self._parent = parent
        self._state = get(state, {})
        self._cleanups = []

    @property
    def parent(self):
        return self._parent

    def cleanup(self, func, *args, **kwargs):
        loop = None

        if asyncio.iscoroutinefunction(func):
            if is_running_in_event_loop():
                loop = asyncio.get_event_loop()

        def func_wrapper():
            """Cleanup function wrapper.
            """
            r = func(*args, **kwargs)

            async def _task(r):
                return await r

            if asyncio.iscoroutine(r):
                if is_running_in_event_loop():
                    async def _async_wrapper():
                        """Process async cleanup function.
                        """
                        if asyncio.get_running_loop() is loop or loop is None:
                            await r
                        else:
                            if loop.is_running():
                                await asyncio.wrap_future(
                                    asyncio.run_coroutine_threadsafe(_task(r), loop=loop))
                            else:
                                with ThreadPoolExecutor(join_on_shutdown=False) as executor:
                                    await wrap_future(executor.submit(loop.run_until_complete, args=(_task(r),)))
                    return _async_wrapper()

                else:
                    if loop is None:
                        asyncio.run(_task(r))
                    else:
                        if loop.is_running():
                            asyncio.run_coroutine_threadsafe(_task(r), loop=loop).result()
                        else:
                            loop.run_until_complete(_task(r))

        self._cleanups.append(func_wrapper)

    def _cleanup(self):
        exc_type, exc_value, exc_traceback = None, None, None
        for func in reversed(self._cleanups):
            try:
                r = func()
                # if func returned a generator as it does for
                # async cleanups then just consume it
                if inspect.isgenerator(r):
                    for i in r:
                        pass
            except StopAsyncIteration:
                pass
            except StopIteration:
                pass
            except (Exception, KeyboardInterrupt) as e:
                if not exc_value:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
        return exc_type, exc_value, exc_traceback

    async def _async_cleanup(self):
        exc_type, exc_value, exc_traceback = None, None, None
        for func in reversed(self._cleanups):
            try:
                r = await func()
                # if func returned a generator as it does for
                # async cleanups then just consume it
                if inspect.isgenerator(r):
                    for i in r:
                        pass
            except StopAsyncIteration:
                pass
            except StopIteration:
                pass
            except (Exception, KeyboardInterrupt) as e:
                if not exc_value:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
        return exc_type, exc_value, exc_traceback

    def __getattr__(self, name):
        try:
            if name.startswith('_'):
                return self.__dict__[name]
        except KeyError:
            raise AttributeError(name) from None

        curr = self
        while True:
            try:
                return curr._state[name]
            except KeyError:
                if curr._parent:
                    curr = curr._parent
                    continue
                raise AttributeError(name) from None

    def __setattr__(self, name, value):
        if name.startswith('_'):
            self.__dict__[name] = value
        else:
            self._state[name] = value

    def __delattr__(self, name):
        try:
            del self._state[name]
        except KeyError:
            raise AttributeError(name) from None

    def __contains__(self, name):
        if name.startswith('_'):
            return name in self.__dict__

        curr = self
        while True:
            if name in curr._state:
                return True
            if curr._parent:
                curr = curr._parent
            else:
                return False

class SharedContext(Context):
    """Share context with parent.
    """
    def __init__(self, parent):
        if not isinstance(parent, Context):
            raise ValueError("parent must be an instance of Context")
        self._parent = parent._parent
        self._state = parent._state
        self._cleanups = parent._cleanups

class TestBase(object):
    """Base class for all the tests.

    :param name: name
    :param flags: flags
    :param parent: parent name
    :param only: tests to run
    :param start: name of the starting test
    :param end: name of the last test
    """
    uid = None
    tags = set()
    attributes = []
    requirements = []
    specifications = []
    examples = None
    name = None
    description = None
    node = None
    map = []
    flags = Flags()
    name_sep = "."
    type = TestType.Test
    subtype = None

    def __init__(self, name=None, flags=None, cflags=None, type=None, subtype=None,
                 uid=None, tags=None, attributes=None, requirements=None, specifications=None,
                 examples=None, description=None, parent=None, parent_type=None, parent_subtype=None,
                 xfails=None, xflags=None, ffails=None, only=None, skip=None,
                 start=None, end=None, only_tags=None, skip_tags=None,
                 args=None, id=None, node=None, map=None, context=None,
                 repeats=None, retries=None, private_key=None, setup=None, first_fail=None, test_to_end=None,
                 parallel_pool_size=None):

        self.lock = threading.Lock()

        if current() is None:
            if top() is not None:
                raise TerminatedError("only one top level test is allowed")
            top(self)
            # flag to indicate if main test called init
            self._init= False

        current_test = current()

        self.io = None
        self.name = name
        if self.name is None:
            raise TypeError("name must be specified")
        self.name = self.name
        self.child_count = 0
        self.start_time = time.time()
        self.test_time = None
        self.parent = parent
        self.parent_type = parent_type
        self.parent_subtype = parent_subtype
        self.id = get(id, [settings.test_id])
        self.id_str = id_sep + id_sep.join(str(n) for n in self.id)
        self.node = get(node, self.node)
        self.map = get(map, list(self.map))
        self.type = get(type, self.type)
        self.subtype = get(subtype, self.subtype)
        self.context = get(context, current_test.context if current_test and self.type < TestType.Iteration else (Context(current_test.context if current_test else None)))
        self.tags = tags
        self.specifications = {s.name: s for s in [Specification(*r) for r in get(specifications, list(self.specifications))]}
        self.requirements = {r.name: r for r in [Requirement(*r) for r in get(requirements, list(self.requirements))]}
        self.attributes = {a.name: a for a in [Attribute(*a) for a in get(attributes, list(self.attributes))]}
        self.args = {k: Argument(k, v) for k,v in get(args, {}).items()}
        self.description = get(description, self.description)
        self.examples = get(examples, get(self.examples, ExamplesTable()))
        if not isinstance(self.examples, ExamplesTable):
            self.examples = ExamplesTable(*self.examples)
        self.result = Null(test=self.name, start_time=self.start_time)
        if flags is not None:
            self.flags = Flags(flags)
        self.cflags = Flags(cflags)
        self.uid = get(uid, self.uid)
        if self.uid is not None:
            self.uid = str(self.uid)
        self.xfails = get(xfails, None)
        self.xflags = get(xflags, None)
        self.ffails = get(ffails, None)
        self.only = get(only, None)
        self.skip = get(skip, None)
        self.start = get(start, None)
        self.end = get(end, None)
        self.only_tags = get(only_tags, None)
        self.skip_tags = get(skip_tags, None)
        self.repeats = get(repeats, None)
        self.retries = get(retries, None)
        self.private_key = get(private_key, None)
        self.caller_test = None
        self.setup = get(setup, None)
        self.futures = []
        self.executor = None
        self.terminating = None
        self.terminated = None
        self.subtests = {}
        self.first_fail = get(first_fail, None)
        self.test_to_end = get(test_to_end, None)
        self.parallel_pool_size = get(parallel_pool_size, None)
        self.tracer = tracing.EventAdapter(tracing.TestAdapter(tracer, self), None, source=str(self))

        if self.setup is not None:
            if isinstance(self.setup, (TestDecorator, TestDefinition)):
                pass
            elif inspect.isfunction(self.setup):
                self.setup = functools.partial(self.setup, self=self)
            else:
                raise TypeError(f"'{self.setup}' is not a valid test type")

    def __reduce__(self):
        raise TypeError("not serializable")

    def __str__(self):
        return f"Test(name={self.name},id={self.id_str})@0x{id(self):x}"

    @classmethod
    def make_name(cls, name, parent=None, args=None, format=True):
        """Make full name.

        :param name: name
        :param parent: parent name
        :param args: arguments to the test
        """
        if args is None:
            args = dict()
        try:
            name = str(name) if name is not None else cls.name
            if name and format:
                name = name.format(**{"$cls": cls}, **args)
        except Exception as exc:
            raise NameError(f"can't format '{name}' using {args} {str(exc)}") from None
        if name is None:
            raise TypeError("name must be specified")
        # '/' is not allowed just like in Unix file names
        # so convert any '/' to U+2215 division slash
        name = name.replace(name_sep, "\u2215")
        return join(get(parent, name_sep), name)

    @classmethod
    def make_description(cls, description, args, format=True):
        if args is None:
            args = dict()
        try:
            description = str(description) if description is not None else None
            if description and format:
                description = description.format(**{"$cls": cls}, **args)
        except Exception as exc:
            raise DescriptionError(f"can't format '{description}' using {args} {str(exc)}") from None
        return description

    @classmethod
    def make_tags(cls, tags):
        return {str(tag) for tag in set(get(tags, cls.tags))}

    def terminate(self, result=Skip, message=None, reason="terminated"):
        """Terminate test.
        """
        with tracing.Event(self.tracer, "terminating") as event_tracer:
            if self.terminating:
                return

            with self.lock:
                if self.terminating:
                    return
                if self.cflags & CLEANUP:
                    return
                self.terminating = True

                self.result = self.result(result(message, reason=reason, test=self.name))

                for subtest in self.subtests.values():
                    event_tracer.debug(f"terminating {subtest}")
                    subtest.terminate()
                self.subtests = {}

    def add_subtest(self, subtest):
        """Add subtest.
        """
        with tracing.Event(self.tracer, f"add_subtest({subtest})") as event_tracer:
            with self.lock:
                event_tracer.debug("got lock")
                self.subtests[subtest.id_str] = subtest
                event_tracer.debug(f"modified subtests dictionary")

            if self.terminating:
                event_tracer.debug("terminating subtest")
                subtest.terminate()

    def remove_subtest(self, subtest):
        """Remove subtest.
        """
        with self.lock:
            self.subtests.pop(subtest.id_str, None)

    def child_id(self):
        with self.lock:
            try:
                return self.id + [self.child_count]
            finally:
                self.child_count += 1

    def clear_end_skip(self):
        with self.lock:
            self.end = None
            self.skip = [The("/*")]

    def clear_start(self):
        with self.lock:
            self.start = None

    def set_result(self, test_result, flags):
        if isinstance(test_result, Fail):
            result = Fail(test=self.name, message=test_result.message)
        else:
            # convert Null into an Error
            result = Error(test=self.name, message=test_result.message)
        
        with self.lock:
            if isinstance(self.result, Error):
                pass
            elif isinstance(test_result, Error) and ERROR_NOT_COUNTED not in flags:
                self.result = self.result(result)
            elif isinstance(test_result, Null) and NULL_NOT_COUNTED not in flags:
                self.result = self.result(result)
            elif isinstance(self.result, Fail):
                pass
            elif isinstance(test_result, Fail) and FAIL_NOT_COUNTED not in flags:
                self.result = self.result(result)
            else:
                pass

    def _enter(self):
        if self is not top():
            if self.flags & MANUAL and not self.flags & SKIP and self.type >= TestType.Test:
                pause()

        self.io = TestIO(self)

        if top() is self:
            self._init = init()
            self.io.output.protocol()
            self.io.output.version()

            self.attributes.update({
                    arg.name: Attribute(name=arg.name, value=arg.value, type=arg.type, group=arg.group, uid=arg.uid)
                    for arg in self.args.values()
                })
            self.args = {}

        self.tracer.debug(f"test start", extra={"event_action": tracing.Action.START})
        self.io.output.test_message()

        if self.flags & PAUSE_BEFORE and not self.flags & SKIP:
            pause()

        self.caller_test = current()
        current(self)

        if top() is self:
            if self.parallel_pool_size:
                settings.global_thread_pool = GlobalThreadPoolExecutor(max_workers=self.parallel_pool_size, join_on_shutdown=False)
                settings.global_async_pool = GlobalAsyncPoolExecutor(max_workers=self.parallel_pool_size, join_on_shutdown=False)
                settings.global_process_pool = GlobalProcessPoolExecutor(max_workers=self.parallel_pool_size, join_on_shutdown=False)

        for pattern, force_fail in (self.ffails or {}).items():
            force_result, force_reason, force_when = force_fail[0], force_fail[1], force_fail[2:]
            force_when = force_when[0] if force_when and force_when[0] is not None else lambda test: True
            if not self.flags & SKIP or (self.flags & SKIP and force_result is Skip):
                if match(self.name, pattern):
                    if force_when(self):
                        raise force_result(reason=force_reason, test=self.name)

        if self.parent:
            with tracing.Event(self.tracer, f"adding {self}({self.name}) as subtest of parent {self.parent}"):
                self.parent.add_subtest(self)

        if self.flags & SKIP:
            raise Skip("skip flag set", test=self.name)

        if self.setup is not None:
            r = self.setup()
            if inspect.isasyncgen(r):
                res = async_next(r)
                self.context.cleanup(run_async_generator, r, consume=True)
            elif inspect.isgenerator(r):
                res = next(r)
                self.context.cleanup(run_generator, r, consume=True)

        return self

    def _exit_process_exception(self, exc_type, exc_value, exc_traceback):
        """Process exception on exit.
        """
        if isinstance(exc_value, ResultException):
            self.result = self.result(exc_value)

        elif isinstance(exc_value, TerminatedError):
            self.result = self.result(Skip(None, reason="terminated", test=self.name))

        elif isinstance(exc_value, AssertionError):
            exception(exc_type, exc_value, exc_traceback, test=self)
            self.result = self.result(Fail(exc_type.__name__ + "\n" + get_exception(exc_type, exc_value, exc_traceback), test=self.name))

        else:
            exception(exc_type, exc_value, exc_traceback, test=self)
            result = Error(exc_type.__name__ + "\n" + get_exception(exc_type, exc_value, exc_traceback), test=self.name)
            self.result = self.result(result)

    def _exit(self, exc_type, exc_value, exc_traceback):
        """Synchronous test exit.
        """
        if not self.io:
            return False

        if top() is self and not self._init:
            return False

        try:
            parallel_exception = None

            if self.parent:
                self.parent.remove_subtest(self)

            if exc_value is not None:
                # terminate any unfinished subtests
                self.terminate()

            # join any left over parallel tests and save parallel exception
            if self.futures:
                try:
                    parallel_join(futures=self.futures, test=self, all=True)
                except (Exception, KeyboardInterrupt) as exc:
                    parallel_exception = exc

            # context cleanups
            if self.type >= TestType.Iteration:
                if self.context._cleanups and not isinstance(self.context, SharedContext):
                    try:
                        with Finally("I clean up"):
                            cleanup_exc_type, cleanup_exc_value, cleanup_exc_traceback = self.context._cleanup()
                            if cleanup_exc_value is not None:
                                raise cleanup_exc_value.with_traceback(cleanup_exc_traceback)
                    except Exception:
                        if not exc_value:
                            self._exit_process_exception(*sys.exc_info())

            # close parallel executor if any
            if self.executor is not None:
                self.executor.__exit__(None, None, None)

            # close global pools if present and opened
            if top() is self:
                if settings.global_thread_pool is not None:
                    settings.global_thread_pool.__exit__(None, None, None)
                if settings.global_async_pool is not None:
                    settings.global_async_pool.__exit__(None, None, None)
                if settings.global_process_pool is not None:
                    settings.global_process_pool.__exit__(None, None, None)

            # set result
            self._exit_result(exc_type, exc_value, exc_traceback, parallel_exception)
        finally:
            self._exit_finally()

        return True

    async def _async_exit(self, exc_type, exc_value, exc_traceback):
        """Asynchronous text exit.
        """
        if not self.io:
            return False
        if top() is self and not self._init:
            return False

        try:
            parallel_exception = None

            if self.parent:
                self.parent.remove_subtest(self)

            if exc_value is not None:
                # terminate any unfinished subtests
                self.terminate()
            self.subtests = {}

            # join any left over parallel tests and save
            try:
                await parallel_join(futures=self.futures, test=self, all=True)
            except (Exception, KeyboardInterrupt) as exc:
                parallel_exception = exc

            # context cleanups
            if self.type >= TestType.Iteration:
                if self.context._cleanups:
                    try:
                        async with Finally("I clean up"):
                            cleanup_exc_type, cleanup_exc_value, cleanup_exc_traceback = \
                                await self.context._async_cleanup()
                            if cleanup_exc_value is not None:
                                raise cleanup_exc_value.with_traceback(cleanup_exc_traceback)
                    except Exception:
                        if not exc_value:
                            self._exit_process_exception(*sys.exc_info())

            # close parallel executor if any
            if self.executor is not None:
                self.executor.__exit__(None, None, None)

            # close global pools if present and opened
            if top() is self:
                if settings.global_thread_pool is not None:
                    settings.global_thread_pool.__exit__(None, None, None)
                if settings.global_async_pool is not None:
                    settings.global_async_pool.__exit__(None, None, None)
                if settings.global_process_pool is not None:
                    settings.global_process_pool.__exit__(None, None, None)

            # set result
            self._exit_result(exc_type, exc_value, exc_traceback, parallel_exception)
        finally:
            self._exit_finally()

        return True

    def _exit_result(self, exc_type, exc_value, exc_traceback, parallel_exception):
        """Set test result on exit.
        """
        # set parallel exception if exc_value is None
        if exc_value is None and parallel_exception is not None:
            exc_type = type(parallel_exception)
            exc_value = parallel_exception
            exc_traceback = parallel_exception.__traceback__

        if exc_value is not None:
            self._exit_process_exception(exc_type, exc_value, exc_traceback)
        else:
            if isinstance(self.result, Null) and self.flags & MANUAL and not self.flags & SKIP:
                try:
                    input(result)
                except Exception:
                    self._exit_process_exception(*sys.exc_info())
            elif isinstance(self.result, Null):
                self.result = self.result(OK(test=self.name))

    def _exit_finally(self):
        """Finalize test exit.
        """
        current(self.caller_test, set_value=True)
        previous(self)

        self._apply_eresult_flags()
        self._apply_xresult_flags()
        self._apply_xfails()

        self.io.output.result(self.result)
        self.test_time = time.time() - self.start_time
        self.result.test_time = self.test_time

        if top() is self:
            self.io.output.stop()
            self.io.close(final=True)
        else:
            self.io.close(flush=self.flags & REMOTE)
        
        self.tracer.debug("test exit", extra={"event_action": tracing.Action.END})

        if not self.flags & SKIP:
            if self.flags & PAUSE_AFTER:
                pause()
            elif self.flags & PAUSE_ON_FAIL and isinstance(self.result, FailResults):
                pause()
            elif self.flags & PAUSE_ON_PASS and isinstance(self.result, PassResults):
                pause()

    def _apply_eresult_flags(self):
        """Apply eresult flags to self.result.
        """
        if not ERESULT in self.flags:
            return

        message_template = f"{self.result.message + ', ' if self.result.message else ''}{self.result} result is converted to %(result)s because %(flag)s flag set"

        if EOK in self.flags:
            if not isinstance(self.result, OK):
                self.result = self.result(Fail(message_template % dict(result="Fail", flag="EOK")))

        if EFAIL in self.flags:
            if not isinstance(self.result, Fail):
                self.result = self.result(Fail(message_template % dict(result="Fail", flag="EFAIL")))
            else:
                self.result = self.result(OK(message_template % dict(result="OK", flag="EFAIL")))

        if EERROR in self.flags:
            if not isinstance(self.result, Error):
                self.result = self.result(Fail(message_template % dict(result="Fail", flag="EERROR")))
            else:
                self.result = self.result(OK(message_template % dict(result="OK", flag="EERROR")))

        if ESKIP in self.flags:
            if not isinstance(self.result, Skip):
                self.result = self.result(Fail(message_template % dict(result="Fail", flag="ESKIP")))
            else:
                self.result = self.result(OK(message_template% dict(result="OK", flag="ESKIP")))

    def _apply_xresult_flags(self):
        """Apply xresult flags to self.result.
        """
        if not XRESULT in self.flags:
            return

        if XOK in self.flags and isinstance(self.result, OK):
            self.result = self.result.xout("XOK flag set")

        if XFAIL in self.flags and isinstance(self.result, Fail):
            self.result = self.result.xout("XFAIL flag set")

        if XERROR in self.flags and isinstance(self.result, Error):
            self.result = self.result.xout("XERROR flag set")

        if XNULL in self.flags and isinstance(self.result, Null):
            self.result = self.result.xout("XNULL flag set")

    def _apply_xfails(self):
        """Apply xfails to self.result.
        """
        if not self.xfails:
            return

        for pattern, xouts in self.xfails.items():
            if match(self.name, pattern):
                for xout in xouts:
                    result, reason = xout[:2]
                    when = xout[2] if len(xout) > 2 else None
                    if when is not None and not when(self):
                        continue
                    if isinstance(self.result, result):
                        self.result = self.result.xout(reason)

    def bind(self, func):
        """Bind function to the current test.

        :param func: function that takes an instance of test
            as the argument named 'test'
        :return: partial function with the 'test' argument set to self
        """
        return functools.partial(func, test=self)

    def message_io(self, name=""):
        """Return an instance of test's message IO
        used to write messages using print() method
        or other methods that takes a file-like
        object.

        Note: only write() and flush() methods
        are supported.

        :param name: name of the stream, default: None
        """
        return self.io.message_io(name=name)

epilog = """
argument values:

pattern
  used to match test names using a unix-like file path pattern that supports wildcards
    '/' path level separator
    '*' matches any zero or more characters including '/' path level separator
    '?' matches any single character
    '[seq]' matches any character in seq
    '[!seq]' matches any character not in seq
    ':' matches any one or more characters but not including '/' path level separator
  for a literal match, wrap the meta-characters in brackets where '[?]' matches the character '?'

type
  test type either 'test','suite','module','scenario', 'feature', or 'any'

""" + common_epilog()


def cli_argparser(kwargs, argparser=None):
    """Command line argument parser.

    :argparser: test specific argument parser
    :return: argument parser
    """
    description = kwargs.get("description")
    if description is not None:
        description = str(description)

    main_parser = ArgumentParserClass(
        prog=sys.argv[0],
        description=description,
        description_prog="Test - Framework",
        epilog=epilog
    )
    test_args_schema = None

    if argparser:
        test_args_schema = argparser(main_parser.add_argument_group('test arguments'))

    parser = main_parser.add_argument_group("common arguments")

    parser.add_argument("--config", "-c", dest ="_config", metavar="yml ...",
                        action="append", default=[],
                        help=("test run YAML configuration file. "
                              "Can be specified more than once "
                              "to apply multiple configuration files that are "
                              "applied left to right"), type=file_type("r"))
    parser.add_argument("--name", dest="_name", metavar="name",
                        help="test run name", type=str, required=False)
    parser.add_argument("--tag", dest="_tags", metavar="value", nargs="+",
                        help="test run tags", type=str, required=False)
    parser.add_argument("--attr", dest="_attrs", metavar="name=value", nargs="+",
                        help="test run attributes", type=key_value_type, required=False)
    parser.add_argument("--only", dest="_only", metavar="pattern", nargs="+",
                        help="run only selected tests", type=str, required=False)
    parser.add_argument("--skip", dest="_skip", metavar="pattern",
                        help="skip selected tests", type=str, nargs="+", required=False)
    parser.add_argument("--start", dest="_start", metavar="pattern", nargs=1,
                        help="start at the selected test", type=str, required=False)
    parser.add_argument("--end", dest="_end", metavar="pattern", nargs=1,
                        help="end at the selected test", type=str, required=False)
    parser.add_argument("--only-tags", dest="_only_tags",
                        help="run only tests with selected tags",
                        type=tags_filter_type, metavar="type:tag,...",
                        nargs="+", required=False)
    parser.add_argument("--skip-tags", dest="_skip_tags",
                        help="skip tests with selected tags",
                        type=tags_filter_type, metavar="type:tag,...",
                        nargs="+", required=False)
    parser.add_argument("--pause-before", dest="_pause_before", metavar="pattern",
                        nargs="+", help="pause before executing selected tests",
                        type=str, required=False)
    parser.add_argument("--pause-after", dest="_pause_after", metavar="pattern",
                        nargs="+", help="pause after executing selected tests",
                        type=str, required=False)
    parser.add_argument("--pause-on-fail", dest="_pause_on_fail", metavar="pattern",
                        nargs="+", help="pause after selected tests on failing result",
                        type=str, required=False)
    parser.add_argument("--pause-on-pass", dest="_pause_on_pass", metavar="pattern",
                        nargs="+", help="pause after selected tests on passing result",
                        type=str, required=False)
    parser.add_argument("--random", dest="_random", action="store_true",
                        help="randomize order of auto loaded tests",
                        required=False, default=None)
    parser.add_argument("--debug", dest="_debug", action="store_true",
                        help="enable debugging mode", default=None)
    parser.add_argument("--no-colors", dest="_no_colors",
                        metavar=onoff_type.metavar,
                        help="disable terminal color highlighting", nargs='?',
                        type=onoff_type, default=NoneValue)
    parser.add_argument("--id", metavar="id", dest="_id", type=str, help="custom test id")
    parser.add_argument("-o", "--output", dest="_output", metavar="format", type=str,
                        choices=output_formats,
                        help=f"""stdout output format, choices are: {output_formats},
                            default: 'nice'""")
    parser.add_argument("-l", "--log", dest="_log", metavar="file", type=str,
                        help=("path to the log file where test output will be stored, "
                              "default: uses temporary log file"))
    parser.add_argument("--show-skipped", dest="_show_skipped", action="store_true",
                        help="show skipped tests, default: False", default=None)
    parser.add_argument("--trim-results", dest="_trim_results",
                        help="enable or disable trimming result messages, default: on",
                        type=onoff_type, metavar=onoff_type.metavar, default=NoneValue)
    parser.add_argument("--repeat", dest="_repeat",
                        help=("repeat a test until it either fails, "
                              "passes or all iterations are completed.\n"
                              "Where `pattern` is a test name pattern, "
                              "`count` is a number times to repeat the test, "
                              "`until` is either {'pass', 'fail', 'complete'} "
                              "(default: 'fail')"),
                        type=repeat_type, metavar="pattern,count[,until]]",
                        nargs="+", required=False)
    parser.add_argument("--retry", dest="_retry",
                        help=("retry a test until it passes or all retries are completed."
                              "\nFailed retry attempts except the last one are ignored. "
                              "Where `pattern` is a test name pattern and "
                              "`count` is a number times to retry the test,"
                              "`timeout` (optional) maximum number of seconds "
                              "to retry (default: None),"
                              "`delay` (optional) delay in seconds between "
                              "retries (default: 0),"
                              "`backoff` (optional) backoff factor (default: 1)"),
                        type=retry_type,
                        metavar="pattern,count[,timeout[,delay[,backoff]]]",
                        nargs="+", required=False)
    parser.add_argument("-r", "--reference", dest="_reference", metavar="log",
                        type=logfile_type("r", encoding="utf-8"),
                        help="reference log file")

    parser.add_argument("--rerun", dest="_rerun", metavar="result", type=str,
                        choices=rerun_results, nargs="+",
                        help=("rerun tests in the --reference log file.\n"
                              f"Where `result` is either {rerun_results}"))
    parser.add_argument("--individually", dest="_individually",
                        action="store_true", default=None,
                        help=("if --rerun is specified then rerun tests in the "
                              "--reference log file individually."))

    parser.add_argument("--parallel", dest="_parallel", type=onoff_type,
                        metavar=onoff_type.metavar,
                        help=("enable or disable parallelism for tests "
                              "that support it, default: on"))
    parser.add_argument("--parallel-pool", dest="_parallel_pool",
                        metavar="size", type=count_type,
                        help=("for parallel tests force to use global parallel "
                              "pool of the specified size"))

    parser.add_argument("--private-key", dest="_private_key",
                        metavar="file", type=rsa_private_key_pem_file_type,
                        help=("RSA private key PEM file that can be "
                              "used to encrypt secrets."))

    exit_group = parser.add_mutually_exclusive_group()
    exit_group.add_argument('--first-fail', dest="_first_fail",
                            action='store_true', default=None,
                            help=("force all tests to be first fail and abort "
                                  "the run on the first failing test"))
    exit_group.add_argument('--test-to-end', dest="_test_to_end",
                            action='store_true', default=None,
                            help=("force all tests to be test to end and continue "
                                  "the run even if one of the tests fails"))

    parser.add_argument("--trace", dest="_trace", 
                        type=trace_level_type, default=None,
                        metavar=trace_level_type.metavar,
                        help="enable low-level test program tracing for debugging "
                             "using Python's logging module at the specified level.")

    if database_module:
        database_module.argparser(parser)

    return main_parser, test_args_schema

def parse_cli_args(kwargs, parser_schema):
    """Parse command line arguments.

    :parser: argument parser
    :return: parsed known arguments
    """
    debug_processed = False

    parser, test_args_schema = parser_schema

    # config file validation schema
    class Deprecated(schema.Hook):
        def __init__(self, *args, **kwargs):
            kwargs["handler"] = self._handler
            super(Deprecated, self).__init__(*args, **kwargs)

        def _handler(self, key, *args):
            raise schema.SchemaError(f"key '{key}' is deprecated; " + (self._error or ""))

    common_args_schema = schema.Schema({
        schema.Optional("name"): str,
        Deprecated("tag", "use 'tags' instead"): object,
        schema.Optional("attrs"): [schema.Use(key_value_type)],
        schema.Optional("tags"): [str],
        schema.Optional("only"): [str],
        schema.Optional("skip"): [str],
        schema.Optional("start"): str,
        schema.Optional("end"): str,
        schema.Optional("only-tags"): [schema.Use(tags_filter_type)],
        schema.Optional("skip-tags"): [schema.Use(tags_filter_type)],
        schema.Optional("pause-before"): [str],
        schema.Optional("pause-after"): [str],
        schema.Optional("random"): bool,
        schema.Optional("debug"): bool,
        schema.Optional("no-colors"): bool,
        schema.Optional("trim-results"): bool,
        schema.Optional("colors"): bool,
        schema.Optional("id"): str,
        schema.Optional("output"): schema.Or(*output_formats, error="key 'output' value is not a valid format"),
        schema.Optional("log"): str,
        schema.Optional("show-skipped"): bool,
        schema.Optional("show-retries"): bool,
        schema.Optional("repeat"): [schema.Use(repeat_type)],
        schema.Optional("retry"): [schema.Use(retry_type)],
        schema.Optional("reference"): str,
        schema.Optional("rerun"): schema.Or(*rerun_results, error="key 'rerun' values is not a value result"),
        schema.Optional("individually"): bool,
        schema.Optional("parallel"): bool,
        schema.Optional("parallel-pool"): schema.Use(count_type),
        schema.Optional("private-key"): schema.Use(rsa_private_key_pem_file_type),
        schema.Optional("first-fail"): bool,
        schema.Optional("test-to-end"): bool,
        schema.Optional("database"): [schema.Use(key_value_type)]
    }, ignore_extra_keys=True)

    try:
        args, unknown = parser.parse_known_args()
        args = vars(args)
        exc = None
        default_config = os.path.join(os.path.expanduser("~"), ".testflows.yml")
        configs = []

        if os.path.exists(default_config):
            configs.insert(0, open(default_config, "r"))

        if args.get("_config"):
            configs += args.pop("_config")

        if args["_no_colors"] is None:
            args["_no_colors"] = True
        elif args["_no_colors"] == NoneValue:
            args["_no_colors"] = None
        if args["_trim_results"] == NoneValue:
            args["_trim_results"] = None

        try:
            configs.reverse()
            for config in configs:
                obj = yaml.safe_load(config) or {}
                test_run_args = obj.pop("test run", {})
                try:
                    if test_args_schema:
                        if not isinstance(test_args_schema, schema.Schema):
                            raise TypeError("argument parser returned invalid config schema")
                        obj = test_args_schema.validate(obj)
                    test_run_args = common_args_schema.validate(test_run_args)
                except schema.SchemaError as e:
                    raise schema.SchemaError("in config " + str(e)) from None
                _args = { f"_{k.replace('-','_')}" : v for k,v in test_run_args.items()}
                _args.update(obj)
                _args.update({k:v for k,v in args.items() if v is not None})
                args = _args
        except Exception as e:
            exc = e
        finally:
            for config in configs:
                config.close()

        settings.debug = get(args.pop("_debug", None), get(settings.debug, False))
        debug_processed = True

        if exc is not None:
            raise exc from None

        if unknown:
            raise ExitWithError(f"unknown argument {unknown}")

        settings.trace = get(args.pop("_trace", None), get(settings.trace, False))
        tracing.configure_tracing()

        settings.no_colors = get(args.pop("_no_colors", None), get(settings.no_colors, False))
        settings.trim_results = get(args.pop("_trim_results", None), get(settings.trim_results, True))

        if args.get("_name"):
            kwargs["name"] = args.pop("_name")

        if args.get("_id"):
            settings.test_id = args.get("_id")
            args.pop("_id")

        if args.get("_log"):
            logfile = os.path.abspath(args.get("_log"))
            settings.write_logfile = logfile
            args.pop("_log")
        else:
            settings.write_logfile = templog_filename()

        settings.read_logfile = settings.write_logfile
        if os.path.exists(settings.write_logfile):
            os.remove(settings.write_logfile)

        settings.output_format = args.pop("_output", None) or "nice"

        if args.get("_database"):
            settings.database = args.pop("_database")

        settings.show_skipped = args.pop("_show_skipped", None) or False
        settings.random_order = args.pop("_random", None) or False

        if args.get("_pause_before"):
            xflags = kwargs.get("xflags", {})
            for pattern in args.get("_pause_before"):
                xflags[pattern] = xflags.get(pattern, [0, 0])
                xflags[pattern][0] |= PAUSE_BEFORE
            kwargs["xflags"] = xflags
            args.pop("_pause_before")

        if args.get("_pause_after"):
            xflags = kwargs.get("xflags", {})
            for pattern in args.get("_pause_after"):
                xflags[pattern] = xflags.get(pattern, [0, 0])
                xflags[pattern][0] |= PAUSE_AFTER
            kwargs["xflags"] = xflags
            args.pop("_pause_after")

        if args.get("_pause_on_pass"):
            xflags = kwargs.get("xflags", {})
            for pattern in args.get("_pause_on_pass"):
                xflags[pattern] = xflags.get(pattern, [0, 0])
                xflags[pattern][0] |= PAUSE_ON_PASS
            kwargs["xflags"] = xflags
            args.pop("_pause_on_pass")

        if args.get("_pause_on_fail"):
            xflags = kwargs.get("xflags", {})
            for pattern in args.get("_pause_on_fail"):
                xflags[pattern] = xflags.get(pattern, [0, 0])
                xflags[pattern][0] |= PAUSE_ON_FAIL
            kwargs["xflags"] = xflags
            args.pop("_pause_on_fail")

        if args.get("_only"):
            only = []
            for pattern in args.pop("_only"):
                only.append(The(pattern))
            kwargs["only"] = only

        if args.get("_skip"):
            skip = []
            for pattern in args.pop("_skip"):
                skip.append(The(pattern))
            kwargs["skip"] = skip

        if args.get("_start"):
            pattern = args.pop("_start")[0]
            kwargs["start"] = The(pattern)

        if args.get("_end"):
            pattern = args.pop("_end")[0]
            kwargs["end"] = The(pattern)

        if args.get("_only_tags"):
            _only_tags = {}
            for item in args.pop("_only_tags"):
                test_type, tags = item
                if test_type not in _only_tags:
                    _only_tags[test_type] = []
                _only_tags[test_type].append(tags)
            kwargs["only_tags"] = OnlyTags(**_only_tags).value

        if args.get("_skip_tags"):
            _skip_tags = {}
            for item in args.pop("_skip_tags"):
                test_type, tags = item
                if test_type not in _skip_tags:
                    _skip_tags[test_type] = []
                _skip_tags[test_type].append(tags)
            kwargs["skip_tags"] = SkipTags(**_skip_tags).value

        if args.get("_tags"):
            kwargs["tags"] = {value for value in args.pop("_tags")}

        if args.get("_attrs"):
            if kwargs.get("attributes", None) is None:
                kwargs["attributes"] = []
            kwargs["attributes"] += [Attribute(item.key, item.value) for item in args.pop("_attrs")]
            for attr in kwargs["attributes"]:
                if args.get(attr.name, None):
                    raise AttributeError(f"use test argument '--{attr.name}' instead of '--attr {attr.name}=<value>'")

        if args.get("_first_fail"):
            kwargs["first_fail"] = args.pop("_first_fail")

        elif args.get("_test_to_end"):
            kwargs["test_to_end"] = args.pop("_test_to_end")

        if args.get("_private_key"):
            kwargs["private_key"] = args.pop("_private_key")

        if args.get("_parallel") in ("no", 0, False):
            kwargs["flags"] = kwargs.get("flags", Flags())
            kwargs["flags"] |= NO_PARALLEL

        if args.get("_parallel_pool"):
            kwargs["parallel_pool_size"] = args.pop("_parallel_pool")

        if args.get("_repeat"):
            repeats = []
            for item in args.pop("_repeat"):
                repeats.append(item)
            kwargs["repeats"] = {r.pattern: (r.count, r.until) for r in repeats}

        if args.get("_retry"):
            retries = []
            for item in args.pop("_retry"):
                retries.append(item)
            kwargs["retries"] = {r.pattern: (r.count, r.timeout, r.delay, r.backoff, r.jitter) for r in retries}

        if args.get("_rerun"):
            rerun_individually = args.pop("_individually", None) or False
            rerun = args.pop("_rerun")

            if not args.get("_reference"):
                raise ExitWithError(f"--reference argument must be specified")

            results = {}
            ResultsLogPipeline(args.pop("_reference"), results, steps=False).run()

            if kwargs.get("only") is None:
                kwargs["only"] = []

            if rerun_individually is True:
                kwargs["rerun_individually"] = []

            RerunTest = namedtuple("RerunTest", "name type tags")
            rerun_tests = []
            result_types = []

            for r in rerun:
                if r == "xouts":
                    result_types += ["XOK", "XFail", "XError", "XNull"]
                elif r == "passes":
                    result_types += ["OK"]
                elif r == "fails":
                    result_types += ["Fail", "Error", "Null"]
                elif r == "ok":
                    result_types += ["OK"]
                elif r == "fail":
                    result_types += ["Fail"]
                elif r == "error":
                    result_types += ["Error"]
                elif r == "null":
                    result_types += ["Null"]
                elif r == "xfail":
                    result_types += ["XFail"]
                elif r == "xerror":
                    result_types += ["XError"]
                elif r == "xnull":
                    result_types += ["XNull"]
                elif r == "xok":
                    result_types += ["XOK"]
                elif r == "skip":
                    result_types += ["Skip"]

            for test in results["tests"].values():
                result = test["result"]
                test_type = getattr(TestType, result["test_type"])
                test_name = result["result_test"]
                test_tags = {tag["tag_value"] for tag in test["test"]["tags"]}

                if test_type >= TestType.Test:
                    if result["result_type"] in result_types:
                        found = False
                        for rerun_test in rerun_tests:
                            if rerun_test.name.startswith(test_name):
                                found = True
                                break
                        if not found:
                            rerun_tests.append(RerunTest(test_name, test_type, test_tags))

                rerun_tests.sort()
                length = len(rerun_tests)

                for i, test in enumerate(rerun_tests):
                    if i+1 < length and rerun_tests[i+1].name.startswith(test.name):
                        rerun_tests.remove(test)
                        i -= 1

            for rerun_test in rerun_tests:
                if rerun_individually is True:
                    name_parts = rerun_test.name.split(name_sep)
                    kwargs["rerun_individually"].append(RerunTest(
                        The(join(name_sep, name_parts[1], ":", *name_parts[2:], "*")),
                        rerun_test.type, rerun_test.tags))
                else:
                    kwargs["only"].append(The(join(rerun_test.name, "*")))

        if args.get("func"):
            func = args.pop("func")
            func(args, kwargs)

        if kwargs.get("private_key"):
            private_key = kwargs.get("private_key")
            for name, value in args.items():
                if isinstance(value, RSASecret):
                    value(public_key=private_key.pubkey)

    except (ExitException, KeyboardInterrupt, Exception) as exc:
        if not debug_processed or settings.debug:
            sys.stderr.write(warning(get_exception(), eol='\n'))
        sys.stderr.write(danger("error: " + str(exc).strip()))
        if isinstance(exc, ExitException):
            sys.exit(exc.exitcode)
        else:
            sys.exit(1)

    return args

class TestDefinition(object):
    """Test definition.

    :param name: name of the test
    :param **kwargs: test class arguments
    """
    type = TestType.Test

    def __new__(cls, name=None, **kwargs):
        kwargs = {k: v.value if isinstance(v, NamedValue) else v for k,v in kwargs.items()}
        run = kwargs.pop("run", None)
        test = kwargs.pop("test", None)
        no_arguments = None

        if kwargs.get("args", None):
            no_arguments = False

        if name is not None:
            kwargs["name"] = name

        def inherit_kwargs(**from_kwargs):
            _kwargs = from_kwargs
            _kwargs["args"] = dict(_kwargs["args"])
            _kwargs.update(kwargs)
            return _kwargs

        if run:
            if isinstance(run, TestDecorator):
                kwargs = inherit_kwargs(**run.func.kwargs)
                kwargs["test"] = run
            elif isinstance(run, TestDefinition):
                kwargs = inherit_kwargs(**run.kwargs, **({"name": run.name} if run.name is not None else {}))
            elif isinstance(run, TestBase) or inspect.isclass(run) and issubclass(run, (TestBase, TestDefinition)):
                kwargs["test"] = run
            else:
                raise TypeError(f"'{run}' is not a valid test type")

        elif test:
            if isinstance(test, TestDecorator):
                kwargs = inherit_kwargs(**test.func.kwargs)
                kwargs["test"] = test
            elif isinstance(test, TestDefinition):
                kwargs = inherit_kwargs(**test.kwargs, **({"name": test.name} if test.name is not None else {}))
            elif isinstance(test, TestBase) or inspect.isclass(test) and issubclass(test, (TestBase, TestDefinition)):
                kwargs["test"] = test
            else:
                raise TypeError(f"'{test}' is not a valid test type")

        self = cls.__create__(**kwargs)
        self.no_arguments = no_arguments

        if run:
            return self()
        return self

    @classmethod
    def __create__(cls,  **kwargs):
        self = super(TestDefinition, cls).__new__(cls)
        self.name = None
        self.test = None
        self.parent = None
        self.kwargs = kwargs
        self.tags = None
        self.parallel = self.kwargs.pop("parallel", None)
        self.remote = self.kwargs.pop("remote", None)
        self.repeats = None
        self.retries = None
        self.rerun_individually = None
        self.repeatable_func = None
        self._with_block_frame = None
        self._enter_exc_info = None
        return self

    def __call__(self, *pargs, **args):
        if pargs:
            raise TypeError(f"only named arguments are allowed but {pargs} positional arguments were passed")

        test = self.kwargs.get("test", None)
        executor = self.kwargs.pop("executor", None)
        
        self.kwargs["args"] = dict(self.kwargs.get("args") or {})
        self.kwargs["args"].update(args)

        self.no_arguments = get(self.no_arguments, not args)

        def callable():
            if is_running_in_event_loop():
                raise RuntimeError("should not be running inside the async event loop")

            if test and isinstance(test, TestDecorator):
                self.repeatable_func = test

                def _test_wrapper():
                    with self as _test:
                        r = test(**self.kwargs["args"])
                        if r is not None:
                            value("return", value=r)
                    return _test.result

                async def _async_test_wrapper():
                    async with self as _test:
                        r = await test(**self.kwargs["args"])
                        if r is not None:
                            value("return", value=r)
                    return _test.result

                if asyncio.iscoroutinefunction(test.func):
                    with AsyncPoolExecutor(join_on_shutdown=False) as executor:
                        return executor.submit(_async_test_wrapper).result()
                else:
                    return _test_wrapper()
            else:
                with self as _test:
                    pass
                return _test.result

        async def async_callable():
            if test and isinstance(test, TestDecorator):
                self.repeatable_func = test
                async with self as _test:
                    if not asyncio.iscoroutinefunction(test.func):
                        with ThreadPoolExecutor(join_on_shutdown=False) as executor:
                            def _wrapper(test):
                                return test(**self.kwargs["args"])
                            r = await asyncio.get_event_loop().run_in_executor(executor, _wrapper, (test,))
                    else:
                        r = await test(**self.kwargs["args"])
                    if r is not None:
                        value("return", value=r)
                return _test.result
            else:
                async with self as _test:
                    pass
                return _test.result

        current_test = current()
        is_async = is_running_in_event_loop()
        is_parallel = self.kwargs.get("flags", Flags()) & PARALLEL or self.parallel
        is_remote = self.kwargs.get("flags", Flags()) & REMOTE or self.remote or (executor and (isinstance(executor, ProcessPoolExecutor)))

        if current_test:
            if current_test.cflags & NO_PARALLEL:
                pass

            elif is_parallel:
                self.kwargs["flags"] = self.kwargs.pop("flags", Flags()) | PARALLEL
                if is_async:
                    executor = settings.global_async_pool or executor
                elif is_remote:
                    executor = settings.global_process_pool or executor
                else:
                    executor = settings.global_thread_pool or executor

                if executor is None:
                    if is_async:
                        executor = current_test.executor or AsyncPoolExecutor(join_on_shutdown=False)
                    elif is_remote:
                        executor = current_test.executor or ProcessPoolExecutor(join_on_shutdown=False)
                    else:
                        executor = current_test.executor or ThreadPoolExecutor(join_on_shutdown=False)
                    
                    if current_test.executor is None:
                        current_test.executor = executor

                if not executor.open:
                    executor.__enter__()

                if isinstance(executor, AsyncPoolExecutor):
                    future = executor.submit(async_callable)
                elif isinstance(executor, ProcessPoolExecutor):
                    self.kwargs["flags"] = self.kwargs.pop("flags", Flags()) | REMOTE
                    future = executor.submit(callable)
                else:
                    future = executor.submit(callable)

                current_test.futures.append(future)

                if is_async:
                    return wrap_future(future, new_future=OptionalFuture())
                return future

        if is_async:
            if is_parallel:
                future = asyncio.ensure_future(async_callable())
                if current_test:
                    current_test.futures.append(future)
                return future
            else:
                return async_callable()

        if is_parallel:
            future = convert_result_to_concurrent_future(callable)
            if current_test:
                current_test.futures.append(future)
            return future

        return callable()

    async def __aenter__(self):
        """Asynchronous test start.
        """
        return self.__enter__(_check_async=False)

    def __enter__(self, _check_async=True):
        """Test start.
        """
        if _check_async and is_running_in_event_loop():
            raise RuntimeError("Use `async with` for asynchronous tests.")

        _check_parallel_context()

        try:
            kwargs = self.kwargs
            kwargs["args"] = dict(kwargs.get("args") or {})

            argparser = kwargs.pop("argparser", None)
            parent = kwargs.pop("parent", None) or current()
            keep_type = kwargs.pop("keep_type", None)
            format_name = kwargs.pop("format_name", False)
            format_description = kwargs.pop("format_description", False)
            top_test = top()

            if not top_test:
                cli_args = parse_cli_args(self.kwargs, cli_argparser(self.kwargs, argparser if not isinstance(argparser, ArgumentParser) else argparser.value))
                kwargs["args"].update({k: v for k,v in cli_args.items() if not k.startswith("_")})

            test = kwargs.pop("test", None)
            kwargs_test = test
            if test and isinstance(test, TestDecorator):
                test = test.func.kwargs.get("test", None)
            test = test if test is not None else TestBase
            if not issubclass(test, TestBase):
                raise TypeError(f"{test} must be subclass of TestBase")

            name = test.make_name(kwargs.pop("name", None), parent.name if parent else None, kwargs["args"], format=format_name)
            kwargs["flags"] = Flags(kwargs.get("flags"))
            kwargs["cflags"] = Flags(kwargs.get("cflags"))

            if (kwargs["flags"] & PARALLEL or self.parallel) and not self.repeatable_func:
                raise RuntimeError("inline test can't be executed in parallel")

            if parent:
                kwargs["parent"] = parent
                kwargs["id"] = parent.child_id()
                kwargs["cflags"] = parent.cflags
                # propagate manual flag if automatic test flag is not set
                if not kwargs["flags"] & AUTO:
                    kwargs["flags"] |= parent.flags & MANUAL
                # propagate xfails, xflags, ffails that prefix match the name of the test
                kwargs["xfails"] = {
                    k: v for k, v in parent.xfails.items() if match(name, k, prefix=True)
                } if parent.xfails else None or kwargs.get("xfails")
                kwargs["xflags"] = {
                    k: v for k, v in parent.xflags.items() if match(name, k, prefix=True)
                } if parent.xflags else None or kwargs.get("xflags")
                kwargs["ffails"] = {
                    k: v for k, v in parent.ffails.items() if match(name, k, prefix=True)
                } if parent.ffails else None or kwargs.get("ffails")
                # propagate only, skip, start, and end
                kwargs["only"] = parent.only or kwargs.get("only")
                kwargs["skip"] = parent.skip or kwargs.get("skip")
                kwargs["start"] = parent.start or kwargs.get("start")
                kwargs["end"] = parent.end or kwargs.get("end")
                kwargs["only_tags"] = parent.only_tags or kwargs.get("only_tags")
                kwargs["skip_tags"] = parent.skip_tags or kwargs.get("skip_tags")
                # propagate repeats
                if parent.repeats and parent.type > TestType.Outline and self.type >= TestType.Outline:
                    kwargs["repeats"] = {
                        k: v for k, v in parent.repeats.items() if match(name, k, prefix=True)
                    } if parent.repeats else None or kwargs.get("repeats")
                # propagate retries
                if parent.retries and parent.type > TestType.Outline and self.type >= TestType.Outline:
                    kwargs["retries"] = {
                        k: v for k, v in parent.retries.items() if match(name, k, prefix=True)
                    } if parent.retries else None or kwargs.get("retries")
                # handle parent test type propagation
                if keep_type is None:
                    self._parent_type_propagation(parent, kwargs)
                # propagate first_fail and test_to_end
                if kwargs["type"] >= TestType.Iteration:
                    kwargs["first_fail"] = parent.first_fail or kwargs.get("first_fail")
                    kwargs["test_to_end"] = parent.test_to_end or kwargs.get("test_to_end")

            self.name = name
            self.tags = test.make_tags(kwargs.pop("tags", None))
            self.description = test.make_description(kwargs.pop("description", None), kwargs["args"], format=format_description)
            self.parent = parent

            # anchor all patterns
            kwargs["xfails"] = {
                absname(k, name if name else name_sep): v for k, v in dict(kwargs.get("xfails") or {}).items()
            } or None
            kwargs["xflags"] = {
                absname(k, name if name else name_sep): v for k, v in dict(kwargs.get("xflags") or {}).items()
            } or None
            kwargs["ffails"] = {
                absname(k, name if name else name_sep): v for k, v in dict(kwargs.get("ffails") or {}).items()
            } or None
            kwargs["repeats"] = {
                absname(k, name if name else name_sep): v for k, v in dict(kwargs.get("repeats") or {}).items()
            } or None
            kwargs["retries"] = {
                absname(k, name if name else name_sep): v for k, v in dict(kwargs.get("retries") or {}).items()
            } or None
            kwargs["only"] = [The(str(f)).at(name if name else name_sep) for f in kwargs.get("only") or []] or None
            kwargs["skip"] = [The(str(f)).at(name if name else name_sep) for f in kwargs.get("skip") or []] or None
            kwargs["start"] = The(str(kwargs.get("start"))).at(name if name else name_sep) if kwargs.get("start") else None
            kwargs["end"] = The(str(kwargs.get("end"))).at(name if name else name_sep) if kwargs.get("end") else None
            kwargs["only_tags"] = kwargs.get("only_tags") or None
            kwargs["skip_tags"] = kwargs.get("skip_tags") or None

            self._apply_xflags(name, kwargs)
            self._apply_start(name, parent, kwargs)
            if top_test:
                self._apply_only_tags(self.type, self.tags, kwargs)
                self._apply_skip_tags(self.type, self.tags, kwargs)
            self._apply_skip(name, kwargs)
            self._apply_end(name, parent, kwargs)
            self._apply_only(name, kwargs)

            if kwargs.get("first_fail"):
                kwargs["flags"] &= ~TE
            elif kwargs.get("test_to_end"):
                kwargs["flags"] |= TE

            # for And subtype we change the subtype to be that of its sibling
            if kwargs.get("subtype") is TestSubType.And:
                sibling = None
                prev = previous()
                if prev and depth(prev.name) == depth(name):
                    sibling = prev
                if not sibling:
                    raise TypeError("`And` subtype can't be used here as it has no sibling from which to inherit the subtype")
                if sibling.type != kwargs["type"]:
                    raise TypeError("`And` subtype can't be used here as it sibling is not of the same type")
                kwargs["subtype"] = sibling.subtype

            # auto set mandatory flag for Background, Given, Finally and Cleanup steps
            if kwargs.get("subtype") in [TestSubType.Background, TestSubType.Given, TestSubType.Finally, TestSubType.Cleanup]:
                kwargs["flags"] |= MANDATORY

            # auto set SETUP flag for Given steps
            if kwargs.get("subtype") in [TestSubType.Background, TestSubType.Given]:
                kwargs["flags"] |= SETUP

            # auto set TE and CLEANUP flag for Finally steps
            if kwargs.get("subtype") in [TestSubType.Finally, TestSubType.Cleanup]:
                kwargs["flags"] |= TE | CLEANUP

            # mark nested retries for RetryIteration test type
            if kwargs["type"] == TestType.RetryIteration:
                if kwargs["cflags"] & RETRY:
                    kwargs["flags"] |= NESTED_RETRY
                kwargs["flags"] |= RETRY

            # should not skip mandatory steps
            if kwargs["flags"] & MANDATORY:
                kwargs["flags"] &= ~SKIP
                kwargs["only"] = None
                kwargs["skip"] = None
                kwargs["start"] = None
                kwargs["end"] = None
                kwargs["only_tags"] = None
                kwargs["skip_tags"] = None

            if not top_test:
                # can't skip, pause before or after top level test
                kwargs["flags"] &= ~SKIP
                kwargs["flags"] &= ~PAUSE_BEFORE
                kwargs["flags"] &= ~PAUSE_AFTER
                kwargs["flags"] &= ~PAUSE_ON_PASS
                kwargs["flags"] &= ~PAUSE_ON_FAIL

            kwargs["cflags"] |= kwargs["flags"] & CFLAGS

            self.repeats = kwargs.pop("repeats", None)
            self.retries = kwargs.pop("retries", None)
            self.rerun_individually = kwargs.pop("rerun_individually", None)

            if self.rerun_individually:
                def transform_pattern(pattern):
                    if isabs(pattern):
                        parts = pattern.split(name_sep)
                        return join(name_sep, parts[1], ":", *parts[2:])
                    return pattern

                # need to fix all anchored patterns
                kwargs["xfails"] = {transform_pattern(k): v for k, v in
                    (kwargs.pop("xfails", {}) or {}).items()} or None
                kwargs["xflags"] = {transform_pattern(k): v for k, v in
                    (kwargs.pop("xflags", {}) or {}).items()} or None
                kwargs["ffails"] = {transform_pattern(k): v for k, v in
                    (kwargs.pop("ffails", {}) or {}).items()} or None
                kwargs["repeats"] = {transform_pattern(k): v for k, v in
                    (kwargs.pop("repeats", {}) or {}).items()} or None
                kwargs["retries"] = {transform_pattern(k): v for k, v in
                    (kwargs.pop("retries", {}) or {}).items()} or None
                kwargs["only"] = [The(transform_pattern(str(f))) for f in kwargs.get("only") or []] or None
                kwargs["skip"] = [The(transform_pattern(str(f))) for f in kwargs.get("skip") or []] or None
                kwargs["start"] = The(transform_pattern(str(kwargs.get("start")))) if kwargs.get("start") else None
                kwargs["end"] = The(transform_pattern(str(kwargs.get("end")))) if kwargs.get("end") else None

            if not kwargs["cflags"] & CLEANUP:
                if parent and parent.terminating:
                    raise TerminatedError("test has been terminated")

            self.test = test(name, tags=self.tags, description=self.description,
                repeats=self.repeats, retries=self.retries, **kwargs)

            if getattr(self, "parent_type", None):
                self.test.parent_type = self.parent_type
            if getattr(self, "parent_subtype", None):
                self.test.parent_subtype = self.parent_subtype

            # indicate that parent is running an outline
            # and if there are any user arguments for an outline
            if isinstance(kwargs_test, TestOutline):
                self.test._run_outline_with_no_arguments = self.no_arguments
                self.test._run_outline = True

            if self.rerun_individually is not None:
                self.trace = sys.gettrace()
                sys.settrace(lambda *args, **kwargs: None)
                inspect.currentframe().f_back.f_trace = functools.partial(
                    self.__rerun_individually__, self.rerun_individually)
                return self.test

            retry = None
            repeat = None

            if self.repeats is not None:
                repeat = self._apply_repeats(name, self.repeats)

            if self.retries is not None:
                retry = self._apply_repeats(name, self.retries)

            if repeat is not None:
                if not self.test.flags & NOT_REPEATABLE:
                    self.test.flags |= REPEATED
            if retry is not None:
                if not self.test.flags & NOT_REPEATABLE:
                    self.test.flags |= RETRIED

            if repeat is not None or retry is not None:
                self.trace = sys.gettrace()
                sys.settrace(lambda *args, **kwargs: None)
                inspect.currentframe().f_back.f_trace = functools.partial(
                    self.__repeat__, repeat, retry)
                return self.test

        except (KeyboardInterrupt, Exception):
            raise

        try:
            return self.test._enter()
        except (KeyboardInterrupt, Exception) as exc:
            if not self.test.io:
                raise

            frame = inspect.currentframe().f_back
            self._with_block_frame = (frame, frame.f_lasti, frame.f_lineno)
            self.trace = sys.gettrace()
            sys.settrace(functools.partial(self.__nop__, *sys.exc_info()))
            return self.test

    def _apply_end(self, name, parent, kwargs):
        end = kwargs.get("end")
        if not end:
            return

        if end.match(name):
            if parent:
                parent.clear_end_skip()

    def _apply_start(self, name, parent, kwargs):
        start = kwargs.get("start")
        if not start:
            return

        if not start.match(name):
            kwargs["flags"] |= SKIP
        elif start.match(name, prefix=False):
            kwargs["start"] = None
            if parent:
                parent.clear_start()

    def _apply_repeats(self, name, repeats):
        if not repeats:
            return

        for k, v in repeats.items():
            if match(name, k, prefix=False):
                return v

    def _apply_only_tags(self, type, tags, kwargs):
        only_tags = (kwargs.get("only_tags", {}) or {}).get(type)
        if not only_tags:
            return

        found = {tag for tag in only_tags if tags >= set(tag)}
        if not len(found) > 0:
            kwargs["flags"] |= SKIP
            kwargs["ffails"] = {"*": (Skip, f"only tags {only_tags}")}

    def _apply_skip_tags(self, type, tags, kwargs):
        skip_tags = (kwargs.get("skip_tags", {}) or {}).get(type)
        if not skip_tags:
            return

        found = {tag for tag in skip_tags if tags >= set(tag)}
        if len(found) > 0:
            kwargs["flags"] |= SKIP
            kwargs["ffails"] = {"*": (Skip, f"skip tags {found}")}

    def _apply_only(self, name, kwargs):
        only = kwargs.get("only")
        if not only:
            return

        found = False
        for item in only:
            if item.match(name):
                found = True
                break

        if not found:
            kwargs["flags"] |= SKIP

    def _apply_skip(self, name, kwargs):
        skip = kwargs.get("skip")
        if not skip:
            return

        for item in skip:
            if item.match(name, prefix=False):
                kwargs["flags"] |= SKIP
                break

    def _apply_xflags(self, name, kwargs):
        xflags = kwargs.get("xflags")
        if not xflags:
            return

        for pattern, item in xflags.items():
            if match(name, pattern):
                set_flags, clear_flags = item[:2]
                when = item[2] if len(item) > 2 else None
                if when is not None and not when(self.parent):
                    continue
                kwargs["flags"] = (kwargs["flags"] & ~Flags(clear_flags)) | Flags(set_flags)

    def _parent_type_propagation(self, parent, kwargs):
        """Propagate parent test type if lower
        and not Iteration or RetryIteration.

        :param parent: parent
        :param kwargs: test's kwargs
        """
        type = kwargs.pop("type", TestType.Test)
        subtype = kwargs.pop("subtype", None)

        parent_type = kwargs.get("parent_type", parent.type)
        parent_subtype = kwargs.get("parent_subtype", parent.subtype)

        if parent_type in (TestType.Iteration, TestType.RetryIteration):
            parent_type = parent.parent_type
            parent_subtype = parent.parent_subtype

        if type in (TestType.Iteration, TestType.RetryIteration):
            pass

        elif int(parent_type) < int(type):
            type = parent_type
            subtype = parent_subtype

        elif subtype is TestSubType.Example:
            type = parent_type

        kwargs["subtype"] = subtype
        kwargs["type"] = type
        kwargs["parent_type"] = parent_type
        kwargs["parent_subtype"] = parent_subtype

    def __repeat__(self, repeat=None, retry=None, *args):
        sys.settrace(self.trace)
        raise TestIteration(repeat, retry)

    def __rerun_individually__(self, patterns, *args):
        sys.settrace(self.trace)
        raise TestRerunIndividually(patterns)

    def __nop__(self, exc_type, exc_value, exc_tb, frame, event, arg):
        sys.settrace(self.trace)
        if not str(frame.f_code.co_name) in ("__aexit__", "__exit__"):
            raise exc_value.with_traceback(exc_tb)
        self._enter_exc_info = (exc_type, exc_value, exc_tb)

    def _cleanup_exception(self, exc_value):
        if settings.debug:
            return
        if exc_value.__context__ is not None:
            if isinstance(exc_value.__context__, (TestIteration, TestRerunIndividually)):
                exc_value.__suppress_context__ = True
                return
            return self._cleanup_exception(exc_value.__context__)

    def _make_complete_traceback(self, exception_traceback, frame, co_filename_filter = "testflows/"):
        tb = namedtuple('tb', ('tb_frame', 'tb_lasti', 'tb_lineno', 'tb_next'))

        def walk_frame(frame, tb_next=None):
            if frame is None:
                return tb_next
            if not settings.debug and co_filename_filter in frame.f_code.co_filename:
                tb_next = tb_next
            else:
                tb_next = tb(frame, frame.f_lasti, frame.f_lineno, tb_next)
            return walk_frame(frame.f_back, tb_next)

        def walk_tb(tb_frame):
            tb_next = None
            if tb_frame.tb_next:
                tb_next = walk_tb(tb_frame.tb_next)

            if tb_frame and not settings.debug and co_filename_filter in tb_frame.tb_frame.f_code.co_filename:
                return tb_next
            else:
                return tb(tb_frame.tb_frame, tb_frame.tb_lasti, tb_frame.tb_lineno, tb_next)

        tb_next = walk_tb(exception_traceback)
        if self._with_block_frame is not None:
            # if self._with_block_frame is set it means an exception was raised
            # in __enter__() during test._enter() call. Now we need to fix
            # traceback so that includes the line where "with" block is defined
            # as it is lost
            _frame, _lasti, _lineno = self._with_block_frame
            if tb_next:
                tb_next = tb_next.tb_next
            if tb_next:
                tb_next = tb_next.tb_next
            tb_next = tb(_frame, _lasti, _lineno, tb_next)
        tb_start = walk_frame(frame.f_back, tb_next)

        return tb_start

    def __exit_process_test_iteration_setup(self, exc_value):
        """Test iteration setup.
        """
        repeat = exc_value.repeat
        retry = exc_value.retry

        self.test._enter()

        if self.repeatable_func is None or self.test.flags & NOT_REPEATABLE:
            raise Error("not repeatable")

        kwargs = dict(self.kwargs)
        args = kwargs.pop("args", {})

        repeat_kwargs = dict(kwargs)
        retry_kwargs = dict(kwargs)

        repeat_kwargs.pop("name", None)
        repeat_kwargs.pop("parent", None)
        repeat_kwargs.pop("parent_type", None)
        repeat_kwargs.pop("parent_subtype", None)
        repeat_kwargs["type"] = TestType.Iteration

        retry_kwargs.pop("name", None)
        retry_kwargs.pop("parent", None)
        retry_kwargs.pop("parent_type", None)
        retry_kwargs.pop("parent_subtype", None)
        retry_kwargs["type"] = TestType.RetryIteration

        repeat_kwargs["flags"] = Flags(repeat_kwargs.get("flags")) & ~PARALLEL
        retry_kwargs["flags"] = Flags(retry_kwargs.get("flags")) & ~PARALLEL

        if repeat is not None:
            _, until = repeat
            if until == "fail":
                repeat_kwargs["flags"] = Flags(repeat_kwargs.get("flags")) & ~TE
            else:
                # pass or complete
                repeat_kwargs["flags"] = Flags(repeat_kwargs.get("flags")) | TE

        return repeat, retry, args, repeat_kwargs, retry_kwargs

    def __exit_process_test_iteration(self, exc_value):
        """Process TestIteration exception.
        """
        if not isinstance(exc_value, TestIteration):
            return

        repeat, retry, args, repeat_kwargs, retry_kwargs = self.__exit_process_test_iteration_setup(exc_value)

        repeat_count, repeat_until = repeat if repeat is not None else (1, None)
        _retry = retry if retry is not None else (1,)
        retry_kwargs_flags = Flags(retry_kwargs.pop("flags", None))

        for i in range(repeat_count):
            parent_type, parent_subtype = (self.test.type, self.test.subtype) if self.test.type not in (Iteration, RetryIteration) else (self.test.parent_type, self.test.parent_subtype)

            with Iteration(name=f"{i}", tags=self.tags, **repeat_kwargs,
                           parent_type=parent_type, parent_subtype=parent_subtype) if repeat is not None else NullStep() as iteration:
                _retries = retries(*_retry)
                while True:
                    r = _retries.__next__(flags=retry_kwargs_flags, tags=self.tags,
                        parent_type=parent_type, parent_subtype=parent_subtype, **retry_kwargs)
                    with r if retry is not None else NullStep() as retry_iteration:
                        if retry_iteration is None:
                            retry_iteration = iteration
                        if isinstance(self.repeatable_func, TestOutline):
                            retry_iteration._run_outline_with_no_arguments = self.no_arguments
                            retry_iteration._run_outline = True
                        self.repeatable_func(**args, __run_as_func__=True)

                    if retry is None:
                        break
                    if isinstance(retry_iteration.result, NonFailResults):
                        break

            if repeat_until and repeat_until == "pass" and isinstance(iteration.result, PassResults):
                break

    async def __exit_async_process_test_iteration(self, exc_value):
        """Process TestIteration exception in asyncronous test.
        """
        if not isinstance(exc_value, TestIteration):
            return

        repeat, retry, args, repeat_kwargs, retry_kwargs = self.__exit_process_test_iteration_setup(exc_value)

        repeat_count, repeat_until = repeat if repeat is not None else (1, None)
        _retry = retry if retry is not None else (1,)
        retry_kwargs_flags = Flags(retry_kwargs.pop("flags", None))

        for i in range(repeat_count):
            parent_type, parent_subtype = (self.test.type, self.test.subtype) if self.test.type not in (Iteration, RetryIteration) else (self.test.parent_type, self.test.parent_subtype)

            async with Iteration(name=f"{i}", tags=self.tags, **repeat_kwargs, parent_type=parent_type, parent_subtype=parent_subtype) if repeat is not None else AsyncNullStep() as iteration:
                _retries = retries(*_retry)
                while True:
                    r = _retries.__next__(flags=retry_kwargs_flags, tags=self.tags,
                        parent_type=parent_type, parent_subtype=parent_subtype, **retry_kwargs)
                    with r if retry is not None else AsyncNullStep() as retry_iteration:
                        if retry_iteration is None:
                            retry_iteration = iteration
                        if isinstance(self.repeatable_func, TestOutline):
                            retry_iteration._run_outline_with_no_arguments = self.no_arguments
                            retry_iteration._run_outline = True
                        await self.repeatable_func(**args, __run_as_func__=True)

                    if retry is None:
                        break
                    if isinstance(retry_iteration.result, NonFailResults):
                        break

            if repeat_until and repeat_until == "pass" and isinstance(iteration.result, PassResults):
                break

    def __exit_process_test_rerun_individually_iteration_setup(self, rerun_test):
        """Setup for an iteration of running test individually.
        """
        __kwargs = dict(self.kwargs)
        __kwargs.pop("name", None)
        __kwargs.pop("parent", None)
        __kwargs["flags"] = Flags(__kwargs.get("flags")) | TE
        __kwargs["type"] = TestType.Iteration
        __args = __kwargs.pop("args", {})

        rerun_name = rerun_test.name.pattern.rstrip(name_sep + "*")

        self._apply_start(rerun_name, self.parent, __kwargs)
        self._apply_only_tags(rerun_test.type, rerun_test.tags, __kwargs)
        self._apply_skip_tags(rerun_test.type, rerun_test.tags, __kwargs)
        self._apply_skip(rerun_name, __kwargs)
        self._apply_end(rerun_name, self.parent, __kwargs)
        self._apply_only(rerun_name, __kwargs)

        __only = [rerun_test.name] + (__kwargs.pop("only", []) or [])

        return rerun_name, __only, __args, __kwargs

    def __exit_process_test_rerun_individually(self, exc_value):
        """Process TestRerunIndividually exception.
        """
        if not isinstance(exc_value, TestRerunIndividually):
            return

        rerun_tests = exc_value.tests

        self.test._enter()

        if self.repeatable_func is None:
            raise Error("not repeatable")

        for i, rerun_test in enumerate(rerun_tests):
            name, only, args, kwargs = self.__exit_process_test_rerun_individually_iteration_setup(rerun_test)

            with Module(name=f"{i}", only=only, tags=self.tags, **kwargs) as iteration:
                if isinstance(self.repeatable_func, TestOutline):
                    iteration._run_outline_with_no_arguments = self.no_arguments
                    iteration._run_outline = True
                self.repeatable_func(**args)

    async def __exit_async_process_test_rerun_individually(self, exc_value):
        """Process TestRerunIndividually exception for asynchronous test.
        """
        if not isinstance(exc_value, TestRerunIndividually):
            return

        rerun_tests = exc_value.tests

        self.test._enter()

        if self.repeatable_func is None:
            raise Error("not repeatable")

        for i, rerun_test in enumerate(rerun_tests):
            name, only, args, kwargs = self.__exit_process_test_rerun_individually_iteration_setup(rerun_test)

            async with Module(name=f"{i}", only=only, tags=self.tags, **kwargs) as iteration:
                if isinstance(self.repeatable_func, TestOutline):
                    iteration._run_outline_with_no_arguments = self.no_arguments
                    iteration._run_outline = True
                await self.repeatable_func(**args)

    def __exit_common(self, exc_type, exc_value, exc_traceback, test__exit__):
        """Common async/sync test exit.
        """
        if not self.parent:
            if not test__exit__:
                if settings.debug:
                    sys.stderr.write(warning(get_exception(exc_type, exc_value, exc_traceback), eol='\n'))
                sys.stderr.write(danger("error: " + str(exc_value).strip()))
                sys.exit(1)
            sys.exit(0 if self.test.result else 1)

        if isinstance(exc_value, KeyboardInterrupt):
            raise KeyboardInterrupt from None

        # if test did not handle the exception in _exit then re-raise it
        if exc_value and not test__exit__:
            raise exc_value from None

        if not self.test.result:
            if isinstance(self.test.result, Fail):
                result = Fail(test=self.parent.name, message=self.test.result.message)
            else:
                # convert Null into an Error
                result = Error(test=self.parent.name, message=self.test.result.message)

            if self.test.type == TestType.RetryIteration and LAST_RETRY not in self.test.flags:
                # don't raise or propagate to a parent a failing result of retry
                # if it is not the last try
                pass
            else:
                if TE not in self.test.flags:
                    raise result from None
                else:
                    self.parent.set_result(self.test.result, self.test.flags)

        return True

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Synchronous text exit.
        """
        frame = inspect.currentframe().f_back

        if self._enter_exc_info:
            exc_type, exc_value, exc_traceback = self._enter_exc_info
        if exc_value:
            self._cleanup_exception(exc_value)
            exc_traceback = self._make_complete_traceback(exc_traceback, frame)
        try:
            if isinstance(exc_value, (TestIteration, TestRerunIndividually)):
                try:
                    self.__exit_process_test_iteration(exc_value)
                    self.__exit_process_test_rerun_individually(exc_value)
                except:
                    try:
                        test__exit__ = self.test._exit(*sys.exc_info())
                    except(KeyboardInterrupt, Exception):
                        raise
                else:
                    try:
                        test__exit__ = self.test._exit(None, None, None)
                    except(KeyboardInterrupt, Exception):
                        raise
            else:
                try:
                    test__exit__ = self.test._exit(exc_type, exc_value, exc_traceback)
                except (KeyboardInterrupt, Exception):
                    raise

            return self.__exit_common(exc_type, exc_value, exc_traceback, test__exit__)

        except (Exception, KeyboardInterrupt) as exc:
            raise

        finally:
            if self.test:
                self.test.terminated = True

    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        """Asynchronous test exit.
        """
        frame = inspect.currentframe().f_back

        if self._enter_exc_info:
            exc_type, exc_value, exc_traceback = self._enter_exc_info
        if exc_value:
            self._cleanup_exception(exc_value)
            exc_traceback = self._make_complete_traceback(exc_traceback, frame)
        try:
            if isinstance(exc_value, (TestIteration, TestRerunIndividually)):
                try:
                    await self.__exit_async_process_test_iteration(exc_value)
                    await self.__exit_async_process_test_rerun_individually(exc_value)
                except:
                    try:
                        test__exit__ = await self.test._async_exit(*sys.exc_info())
                    except(KeyboardInterrupt, Exception):
                        raise
                else:
                    try:
                        test__exit__ = await self.test._async_exit(None, None, None)
                    except(KeyboardInterrupt, Exception):
                        raise
            else:
                try:
                    test__exit__ = await self.test._async_exit(exc_type, exc_value, exc_traceback)
                except (KeyboardInterrupt, Exception):
                    raise

            return self.__exit_common(exc_type, exc_value, exc_traceback, test__exit__)

        except (Exception, KeyboardInterrupt) as exc:
            raise
        
        finally:
            if self.test:
                self.test.terminated = True

class Module(TestDefinition):
    """Module definition."""
    type = TestType.Module

    def __new__(cls, name=None, **kwargs):
        kwargs["type"] = TestType.Module
        return super(Module, cls).__new__(cls, name, **kwargs)

class Suite(TestDefinition):
    """Suite definition."""
    type = TestType.Suite

    def __new__(cls, name=None, **kwargs):
        kwargs["type"] = TestType.Suite
        return super(Suite, cls).__new__(cls, name, **kwargs)

class Outline(TestDefinition):
    """Outline definition."""
    type = TestType.Outline

    def __new__(cls, name=None, **kwargs):
        kwargs["type"] = kwargs.pop("type", cls.type)
        return super(Outline, cls).__new__(cls, name, **kwargs)

class Test(TestDefinition):
    """Test definition."""
    type = TestType.Test

    def __new__(cls, name=None, **kwargs):
        kwargs["type"] = TestType.Test
        return super(Test, cls).__new__(cls, name, **kwargs)

class Iteration(TestDefinition):
    """Test iteration definition."""
    type = TestType.Iteration

    def __new__(cls, name=None, **kwargs):
        kwargs["type"] = TestType.Iteration
        parent_type = kwargs.pop("parent_type", TestType.Test)
        parent_subtype = kwargs.pop("parent_subtype", None)
        self = super(Iteration, cls).__new__(cls, name, **kwargs, parent_type=parent_type, parent_subtype=parent_subtype)
        return self

class RetryIteration(TestDefinition):
    """Test retry iteration definition."""
    type = TestType.RetryIteration

    def __new__(cls, name=None, **kwargs):
        kwargs["type"] = TestType.RetryIteration
        parent_type = kwargs.pop("parent_type", TestType.Test)
        parent_subtype = kwargs.pop("parent_subtype", None)
        self = super(RetryIteration, cls).__new__(cls, name, **kwargs, parent_type=parent_type, parent_subtype=parent_subtype)
        return self

class Example(TestDefinition):
    """Example definition."""
    def __new__(cls, name=None, **kwargs):
        kwargs["type"] = kwargs.pop("type", cls.type)
        kwargs["subtype"] = TestSubType.Example
        self = super(Example, cls).__new__(cls, name, **kwargs)
        return self

class Step(TestDefinition):
    """Step definition."""
    type = TestType.Step
    subtype = None

    def __new__(cls, name=None, **kwargs):
        kwargs["type"] = kwargs.pop("type", cls.type)
        kwargs["subtype"] = kwargs.pop("subtype", cls.subtype)
        return super(Step, cls).__new__(cls, name, **kwargs)

# support for BDD
class Feature(Suite):
    def __new__(cls, name=None, **kwargs):
        kwargs["subtype"] = TestSubType.Feature
        return super(Feature, cls).__new__(cls, name, **kwargs)

class Scenario(Test):
    def __new__(cls, name=None, **kwargs):
        kwargs["subtype"] = TestSubType.Scenario
        return super(Scenario, cls).__new__(cls, name, **kwargs)

class Check(Test):
    def __new__(cls, name=None, **kwargs):
        kwargs["subtype"] = TestSubType.Check
        return super(Check, cls).__new__(cls, name, **kwargs)

class Critical(Test):
    def __new__(cls, name=None, **kwargs):
        kwargs["subtype"] = TestSubType.Critical
        return super(Critical, cls).__new__(cls, name, **kwargs)

class Major(Test):
    def __new__(cls, name=None, **kwargs):
        kwargs["subtype"] = TestSubType.Major
        return super(Major, cls).__new__(cls, name, **kwargs)

class Minor(Test):
    def __new__(cls, name=None, **kwargs):
        kwargs["subtype"] = TestSubType.Minor
        return super(Minor, cls).__new__(cls, name, **kwargs)

class Background(Step):
    subtype = TestSubType.Background

class Given(Step):
    subtype = TestSubType.Given

class When(Step):
    subtype = TestSubType.When

class Then(Step):
    subtype = TestSubType.Then

class And(Step):
    subtype = TestSubType.And

class But(Step):
    subtype = TestSubType.But

class By(Step):
    subtype = TestSubType.By

class Finally(Step):
    subtype = TestSubType.Finally

class Cleanup(Step):
    subtype = TestSubType.Cleanup

class NullStep():
    def __enter__(self):
        return None

    def __exit__(self, *args, **kwargs):
        return False

class AsyncNullStep():
    async def __aenter__(self):
        return None

    async def __aexit__(self, *args, **kwargs):
        return False

# decorators
class TestDecorator(object):
    type = Test

    def __init__(self, func):
        self.func = func

        self.func.type = self.type.type
        self.func.name = getattr(self.func, "name", self.func.__name__.replace("_", " "))
        self.func.description = getattr(self.func, "description", self.func.__doc__)

        signature = inspect.signature(self.func)

        args = getattr(self.func, "args", {})
        default_args = {p.name: p.default for p in signature.parameters.values() if
            p.default != inspect.Parameter.empty}

        self.func.args = default_args
        self.func.args.update(args)

        kwargs = dict(vars(self.func))

        self.func.kwargs = kwargs

        if asyncio.iscoroutinefunction(self.func):
            self.func.kwargs["flags"] = Flags(self.func.kwargs.pop("flags", None)) | ASYNC

        _type = self.type
        functools.update_wrapper(self, self.func)
        self.type = _type

    def __call__(self, *pargs, **args):
        if pargs:
            raise TypeError(f"only named arguments are allowed but {pargs} positional arguments were passed")

        if is_running_in_event_loop():
            if not (asyncio.iscoroutinefunction(self.func) or inspect.isasyncgenfunction(self.func)):
                with ThreadPoolExecutor(join_on_shutdown=False) as executor:
                    def _wrapper():
                        return self.__run__(**args)
                    r = asyncio.get_event_loop().run_in_executor(executor, _wrapper)
                    current().futures.append(r)
                    return r

        if asyncio.iscoroutinefunction(self.func) or inspect.isasyncgenfunction(self.func):
            async def _runner():
                return await self.__run__(**args)

            if not is_running_in_event_loop():
                current_test = current()
                executor = current_test.executor if current_test else None
                if not isinstance(executor, AsyncPoolExecutor):
                     with AsyncPoolExecutor(join_on_shutdown=False) as executor:
                        return executor.submit(_runner).result()
                else:
                    executor = settings.global_async_pool or executor

                    if not executor.open:
                        executor.__enter__()

                    return executor.submit(_runner).result()
            else:
                return _runner()

        return self.__run__(**args)

    def __run__(self, **args):
        _run_as_func = args.pop("__run_as_func__", False)

        _check_parallel_context()

        test = current()

        def process_func_result(r):
            if inspect.isasyncgen(r):
                res = run_async_generator(r)
                test.context.cleanup(run_async_generator, r, consume=True)
                r = res
            elif inspect.isgenerator(r):
                res = run_generator(r)
                test.context.cleanup(run_generator, r, consume=True)
                r = res

            return r

        def run(test):
            return process_func_result(self.func(test, **args))

        test_running_outline = getattr(test, "_run_outline", False)

        if (test is None
                or (test and test.type > self.type.type and self.type.type != TestType.Outline)
                or (test and test_running_outline)) and not (test and _run_as_func):
            kwargs = dict(self.func.kwargs)

            if isinstance(self, TestOutline):
                no_arguments = not args or getattr(test, "_run_outline_with_no_arguments", False)
                examples = test_running_outline and getattr(test, "examples") or self.examples

                if no_arguments and examples:
                    kwargs["args"] = {}
                    kwargs.pop("test", None)

                    _test_type = self.type(**kwargs, test=self)

                    def execute_examples():
                        for example in examples:
                            _kwargs = dict(self.func.kwargs)
                            _kwargs["name"] = str(example)
                            _kwargs["args"] = dict(kwargs.get("args", {}))
                            _kwargs["args"].update(vars(example))
                            _kwargs.update(dict(examples.args))
                            _kwargs.update(dict(example._args))
                            _kwargs.pop("type", None)
                            _kwargs.pop("examples", None)

                            if _test.type in (TestType.Iteration, TestType.RetryIteration):
                                type = _test.parent_type
                            else:
                                type = _test.type

                            _example_type = Example(type=type, **_kwargs)

                            def execute_example(**args):
                                process_func_result(self.func(current(), **args))

                            _example_type.repeatable_func = execute_example

                            with _example_type as _example:
                                execute_example(**vars(example))

                    _test_type.repeatable_func = execute_examples

                    if test and test_running_outline:
                        _test = test
                        execute_examples()
                    else:
                        with _test_type as _test:
                            execute_examples()

                    return _test
                else:
                    if test and test_running_outline:
                        return run(test)
                    else:
                        kwargs.pop("test", None)
                        return self.type(**kwargs, test=self)(**args)
            else:
                kwargs.pop("test", None)
                return self.type(**kwargs, test=self)(**args)
        else:
            return run(test)

class TestStep(TestDecorator):
    type = Step
    subtype = None

    def __init__(self, func_or_subtype=None):
        self.func = None

        if inspect.isfunction(func_or_subtype):
            self.func = func_or_subtype
        elif func_or_subtype is not None:
            self.subtype = func_or_subtype.subtype

        if self.func:
            TestDecorator.__init__(self, self.func)

    def __call__(self, *args, **kwargs):
        if not self.func:
            self.func = args[0]
            if self.subtype is not None:
                self.func.subtype = self.subtype
            TestDecorator.__init__(self, self.func)
            return self

        return super(TestStep, self).__call__(*args, **kwargs)

class TestOutline(TestDecorator):
    type = Outline

    def __init__(self, func_or_type=None):
        self.func = None
        self.examples = None

        if inspect.isfunction(func_or_type):
            self.func = func_or_type
        elif func_or_type is not None:
            self.type = func_or_type

        if self.func:
            self._init_func()
            TestDecorator.__init__(self, self.func)

    def _init_func(self):
        if getattr(self.func, "examples", None):
            self.examples = self.func.examples

    def __call__(self, *args, **kwargs):
        if not self.func:
            self.func = args[0]
            self._init_func()
            TestDecorator.__init__(self, self.func)
            return self

        return super(TestOutline, self).__call__(*args, **kwargs)

class TestCase(TestDecorator):
    type = Test

class TestScenario(TestCase):
    type = Scenario

class TestCheck(TestCase):
    type = Check

class TestCritical(TestCase):
    type = Critical

class TestMajor(TestCase):
    type = Major

class TestMinor(TestCase):
    type = Minor

class TestSuite(TestDecorator):
    type = Suite

class TestFeature(TestSuite):
    type = Feature

class TestModule(TestDecorator):
    type = Module

class TestBackground(TestDecorator):
    type = Background

def ordered(tests):
    """Return ordered list of tests.
    """
    if settings.random_order:
        random.shuffle(tests)
    else:
        human_sort(tests, key=lambda test: test.__name__)
    return tests

def loads(name, *types, package=None, frame=None, filter=None):
    """Load multiple tests from module.

    :param name: module name or module
    :param *types: test types (Step, Test, Scenario, Suite, Feature, or Module), default: all
    :param package: package name if module name is relative (optional)
    :param frame: caller frame if module name is not specified (optional)
    :param filter: filter function
    :return: list of tests
    """
    if name is None or name == ".":
        if frame is None:
            frame = inspect.currentframe().f_back
        module = sys.modules[frame.f_globals["__name__"]]
    elif inspect.ismodule(name):
        module = name
    else:
        module = importlib.import_module(name, package=package)

    def is_type(member):
        if isinstance(member, TestDecorator):
            if not types:
                return True
            return member.type in types

    tests = ordered([test for name, test in inspect.getmembers(module, is_type)])

    if filter:
        return builtins.filter(filter, tests)

    return tests

class retries(object):
    """Retries object to retry some piece of inline code until it succeeds
    and no exception is raised.

    ```python
    for retry in retries(timeout=30, delay=0):
        with retry:
            my_code()
    ```

    :param count: number of retries, default: None
    :param timeout: timeout in sec, default: None
    :param delay: delay in sec between retries, default: 0 sec
    :param backoff: backoff multiplier that is applied to the delay, default: 1
    :param jitter: jitter added to delay between retries specified as
                   a tuple(min, max), default: (0,0)
    """
    def __init__(self, count=None, timeout=None, delay=0, backoff=1, jitter=None):
        self.count = int(count) if count is not None else None
        self.timeout = float(timeout) if timeout is not None else None
        self.delay = float(delay)
        self.backoff = backoff
        self.jitter = tuple(jitter) if jitter else tuple([0, 0])
        self.delay_with_backoff = self.delay
        self.started = None
        self.number = -1
        self.retry = None

    def __iter__(self):
        # re-initialize state
        self.delay_with_backoff = self.delay
        self.number = -1
        self.started = None
        return self

    def __next__(self, **kwargs):
        flags = kwargs.pop("flags", Flags())
        current_type = current().type
        parent_type = kwargs.pop("parent_type", current_type if current_type not in (Iteration, RetryIteration) else current().parent_type)
        parent_subtype = kwargs.pop("parent_subtype", current_type if current_type not in (Iteration, RetryIteration) else current().parent_subtype)

        if self.retry is not None:
            if self.retry.test is not None:
                if isinstance(self.retry.test.result, NonFailResults):
                    raise StopIteration

        if self.started and self.delay_with_backoff:
            if self.backoff:
                self.delay_with_backoff *= self.backoff

            delay = self.delay_with_backoff
            if self.jitter:
                delay += random.uniform(*self.jitter)

            if self.timeout is not None:
                delay = min(delay, max(0, self.timeout - (time.time() - self.started)))

            time.sleep(delay)

        if self.started and self.timeout is not None and time.time() - self.started >= self.timeout:
            flags |= LAST_RETRY
            flags &= ~TE

        if not self.started:
            self.started = time.time()

        self.number += 1

        if self.count is not None and self.count <= self.number + 1:
            flags |= LAST_RETRY
            flags &= ~TE

        self.retry = RetryIteration(f"try #{self.number}", flags=flags, parent_type=parent_type, parent_subtype=parent_subtype, **kwargs)

        return self.retry

def retry(func, count=None, timeout=None, delay=0, backoff=1, jitter=None):
    """Retry function.

    For example,

    ```python
    retry(my_func, count=5, timeout=30)(*my_args, **kwargs)
    ```

    :param func: function to retry
    :param count: number of retries, default: None
    :param timeout: timeout in sec, default: None
    :param delay: delay in sec between retries, default: 0 sec
    :param backoff: backoff multiplier that is applied to the delay, default: 1
    :param jitter: jitter added to delay between retries specified as
                   a tuple(min, max), default: (0,0)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        for _retry in retries(count=count, timeout=timeout, delay=delay, backoff=backoff, jitter=jitter):
            with _retry:
                return func(*args, **kwargs)

    return wrapper

class repeats(object):
    """Repeat object to repeat some piece of inline code until it succeeds.

    ```python
    for iteration in repeats(count=30, until="complete", delay=0):
        with iteration:
            my_code()
    ```

    :param count: number of iterations, default: None
    :param until: stop condition, either 'pass', 'fail', or 'complete', default: 'complete'  
    :param delay: delay in sec between iterations, default: 0 sec
    :param backoff: backoff multiplier that is applied to the delay, default: 1
    :param jitter: jitter added to delay between retries specified as
                   a tuple(min, max), default: (0,0)
    """

    def __init__(self, count=None, until="complete", delay=0, backoff=1, jitter=None):
        self.count = int(count) if count is not None else None
        self.until = str(until)
        self.delay = float(delay)
        self.backoff = backoff
        self.jitter = tuple(jitter) if jitter else tuple([0, 0])
        self.delay_with_backoff = self.delay
        self.number = -1
        self.started = None
        self.iteration = None

    def __iter__(self):
        # re-initialize state
        self.delay_with_backoff = self.delay
        self.number = -1
        self.started = None
        return self

    def __next__(self, **kwargs):
        flags = kwargs.pop("flags", Flags())
        current_type = current().type
        parent_type = kwargs.pop("parent_type", current_type if current_type not in (Iteration, RetryIteration) else current().parent_type)
        parent_subtype = kwargs.pop("parent_subtype", current_type if current_type not in (Iteration, RetryIteration) else current().parent_subtype)

        if self.until in ("pass", "complete"):
            flags |=  TE

        if self.iteration is not None:
            if self.iteration.test is not None:
                if self.until == "pass" and isinstance(self.iteration.test.result, NonFailResults):
                    raise StopIteration
                elif self.until == "fail" and isinstance(self.iteration.test.result, FailResults):
                    raise StopIteration
                elif self.number + 1 == self.count:
                    raise StopIteration

        if self.started and self.delay_with_backoff:
            if self.backoff:
                self.delay_with_backoff *= self.backoff

            delay = self.delay_with_backoff
            if self.jitter:
                delay += random.uniform(*self.jitter)

            time.sleep(delay)

        if not self.started:
            self.started = time.time()

        self.number += 1

        if self.count is not None and self.count <= self.number + 1:
            flags &= ~TE

        self.iteration = Iteration(f"run #{self.number}", flags=flags, parent_type=parent_type, parent_subtype=parent_subtype, **kwargs)

        return self.iteration

def repeat(func, count=None, until="complete", delay=0, backoff=1, jitter=None):
    """Repeat function and return a list of the results for each iteration.

    For example,

    ```python
    repeat(my_func, count=5, until="complete")(*my_args, **kwargs)
    ```

    :param func: function to repeat
    :param count: number of iterations, default: None
    :param until: stop condition, either 'pass', 'fail', or 'complete', default: 'complete' 
    :param timeout: timeout in sec, default: None
    :param delay: delay in sec between iterations, default: 0 sec
    :param backoff: backoff multiplier that is applied to the delay, default: 1
    :param jitter: jitter added to delay between repeats specified as
                   a tuple(min, max), default: (0,0)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        results = []
        for _iter in repeats(count=count, until=until, delay=delay, backoff=backoff, jitter=jitter):
            with _iter:
                try:
                    results.append(func(*args, **kwargs))
                except Exception as e:
                    results.append(e)
                    raise
        return results

    return wrapper
