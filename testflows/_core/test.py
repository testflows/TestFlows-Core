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
import os
import sys
import time
import inspect
import functools
import tempfile
import threading
import textwrap

from contextlib import ExitStack, contextmanager

import testflows.settings as settings

from .exceptions import DummyTestException, ArgumentError, ResultException, RepeatTestException
from .flags import Flags, SKIP, TE, FAIL_NOT_COUNTED, ERROR_NOT_COUNTED, NULL_NOT_COUNTED
from .flags import CFLAGS, PAUSE_BEFORE, PAUSE_AFTER
from .testtype import TestType, TestSubType
from .objects import get, Null, OK, Fail, Skip, Error, Argument, Attribute, ExamplesTable
from .constants import name_sep, id_sep
from .io import TestIO, LogWriter
from .name import join, depth, match, absname
from .funcs import current, top, previous, main, skip, ok, fail, error, exception, pause, load
from .init import init
from .cli.arg.parser import ArgumentParser
from .cli.arg.exit import ExitWithError, ExitException
from .cli.arg.type import key_value as key_value_type
from .cli.text import danger, warning
from .exceptions import exception as get_exception
from .filters import the

class xfails(dict):
    """xfails container.

    xfails = {
        "pattern": [("result", "reason")],
        ...
        }
    """
    def add(self, pattern, *results):
        """Add an entry to the xfails.

        :param pattern: test name pattern to match
        :param *results: one or more results to cross out
            where each result is a two-tuple of (result, reason)
        """
        self[pattern] = results
        return self

class xflags(dict):
    """xflags container.

    xflags = {
        "filter": (set_flags, clear_flags),
        ... 
    }
    """
    def add(self, pattern, set_flags=0, clear_flags=0):
        """Add an entry to the xflags.

        :param pattern: test name pattern to match
        :param set_flags: flags to set
        :param clear_flags: flags to clear, default: None
        """
        self[pattern] = [Flags(set_flags), Flags(clear_flags)]
        return self

class DummyTest(object):
    """Base class for dummy tests.
    """
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        def dummy(*args, **kwargs):
            pass

        self.trace = sys.gettrace()
        sys.settrace(dummy)
        sys._getframe(1).f_trace = self.__skip__

    def __skip__(self, *args):
        sys.settrace(self.trace)
        raise DummyTestException()

    def __exit__(self, exception_type, exception_value, exception_traceback):
        if isinstance(exception_value, DummyTestException):
            return True

class TestContext(object):
    """Test context.
    """
    def __init__(self, parent, state=None):
        self._parent = parent
        self._state = get(state, {})
        self._cleanups = []

    def cleanup(self, func, *args, **kwargs):
        def func_wrapper():
            func(*args, **kwargs)
        self._cleanups.append(func_wrapper)

    def _cleanup(self):
        exc_type, exc_value, exc_traceback = None, None, None
        for func in reversed(self._cleanups):
            try:
                func()
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
    users = []
    tickets = []
    examples = None
    name = None
    description = None
    node = None
    map = None
    flags = Flags()
    name_sep = "."
    type = TestType.Test
    subtype = TestSubType.Empty

    @classmethod
    def argparser(cls):
        """Command line argument parser.

        :return: argument parser
        """
        definitions_description = """
        
        Option values
        
        pattern 
          used to match test names using a unix-like file path pattern that supports wildcards
            '/' path level separator
            '*' matches everything
            '?' matches any single character
            '[seq]' matches any character in seq
            '[!seq]' matches any character not in seq
            ':' matches anything at the current path level
          for example: "suiteA/*" selects all the tests in 'suiteA'
        """
        parser = ArgumentParser(
                prog=sys.argv[0],
                description=((cls.description or "") + definitions_description),
                description_prog="Test - Framework"
            )
        parser.add_argument("--name", dest="_name", metavar="name",
            help="test run name", type=str, required=False)
        parser.add_argument("--tag", dest="_tags", metavar="value", nargs="+",
            help="test run tags", type=str, required=False)
        parser.add_argument("--attr", dest="_attrs", metavar="name=value", nargs="+",
            help="test run attributes", type=key_value_type, required=False)
        parser.add_argument("--only", dest="_only", metavar="pattern", nargs="+",
            help="run only selected tests", type=str, required=False)
        parser.add_argument("--skip", dest="_skip", metavar="pattern", nargs="+",
            help="skip selected tests", type=str, required=False)
        parser.add_argument("--start", dest="_start", metavar="pattern", nargs=1,
            help="start at the selected test", type=str, required=False)
        parser.add_argument("--end", dest="_end", metavar="pattern", nargs=1,
            help="end at the selected test", type=str, required=False)
        parser.add_argument("--pause-before", dest="_pause_before", metavar="pattern", nargs="+",
            help="pause before executing selected tests", type=str, required=False)
        parser.add_argument("--pause-after", dest="_pause_after", metavar="pattern", nargs="+",
            help="pause after executing selected tests", type=str, required=False)
        parser.add_argument("--debug", dest="_debug", action="store_true",
            help="enable debugging mode", default=False)
        parser.add_argument("--no-colors", dest="_no_colors", action="store_true",
            help="disable terminal color highlighting", default=False)
        parser.add_argument("--id", metavar="id", dest="_id", type=str, help="custom test id")
        parser.add_argument("-o", "--output", dest="_output", metavar="format", type=str,
            choices=["slick", "nice", "quiet", "short", "dots", "raw", "silent"], default="nice",
            help="""stdout output format, choices are: ['slick','nice','short','dots','quiet','raw','silent'],
                default: 'nice'""")
        parser.add_argument("-l", "--log", dest="_log", metavar="file", type=str,
            help="path to the log file where test output will be stored, default: uses temporary log file")
        parser.add_argument("--show-skipped", dest="_show_skipped", action="store_true",
            help="show skipped tests, default: False", default=False)
        return parser

    def parse_cli_args(self, xflags=None, only=None, skip=None, start=None, end=None,
            name=None, tags=None, attributes=None):
        """Parse command line arguments.

        :return: parsed known arguments
        """
        try:
            parser = self.argparser()
            args, unknown = parser.parse_known_args()
            args = vars(args)

            if args.get("_name"):
                name = args.pop("_name")

            if name is None:
                raise TypeError("name must be specified")

            if args.get("_debug"):
                settings.debug = True
                args.pop("_debug")

            if args.get("_no_colors"):
                settings.no_colors = True
                args.pop("_no_colors")

            if unknown:
                raise ExitWithError(f"unknown argument {unknown}")

            if args.get("_id"):
                settings.test_id = args.get("_id")
                args.pop("_id")

            if args.get("_log"):
                logfile = os.path.abspath(args.get("_log"))
                settings.write_logfile = logfile
                args.pop("_log")
            else:
                settings.write_logfile = os.path.join(tempfile.gettempdir(), f"testflows.{os.getpid()}.log")

            settings.read_logfile = settings.write_logfile
            if os.path.exists(settings.write_logfile):
                os.remove(settings.write_logfile)

            settings.output_format = args.pop("_output")

            if args.get("_show_skipped"):
                settings.show_skipped = True
                args.pop("_show_skipped")

            if args.get("_pause_before"):
                if not xflags:
                    xflags = globals()["xflags"]()
                for pattern in args.get("_pause_before"):
                    pattern = absname(pattern, name)
                    xflags[pattern] = xflags.get(pattern, [0, 0])
                    xflags[pattern][0] |= PAUSE_BEFORE
                args.pop("_pause_before")

            if args.get("_pause_after"):
                if not xflags:
                    xflags = globals()["xflags"]()
                for pattern in args.get("_pause_after"):
                    pattern = absname(pattern, name)
                    xflags[pattern] = xflags.get(pattern, [0, 0])
                    xflags[pattern][0] |= PAUSE_AFTER
                args.pop("_pause_after")

            if args.get("_only"):
                only = [] # clear whatever was passed
                for pattern in args.get("_only"):
                    only.append(the(pattern).at(name))
                args.pop("_only")

            if args.get("_skip"):
                skip = [] # clear whatever was passed
                for pattern in args.get("_skip"):
                    only.append(the(pattern).at(name))
                args.pop("_skip")

            if args.get("_start"):
                start = the(args.get("_start")[0]).at(name)
                args.pop("_start")

            if args.get("_end"):
                end = the(args.get("_end")[0]).at(name)
                args.pop("_end")

            if args.get("_tags"):
                tags = [value for value in args.pop("_tags")]

            if args.get("_attrs"):
                attributes = [Attribute(item.key, item.value) for item in args.pop("_attrs")]

        except (ExitException, KeyboardInterrupt, Exception) as exc:
            #if settings.debug:
            sys.stderr.write(warning(get_exception(), eol='\n'))
            sys.stderr.write(danger("error: " + str(exc).strip()))
            if isinstance(exc, ExitException):
                sys.exit(exc.exitcode)
            else:
                sys.exit(1)

        return args, xflags, only, skip, start, end, name, tags, attributes

    def __init__(self, name=None, flags=None, cflags=None, type=None, subtype=None,
                 uid=None, tags=None, attributes=None, requirements=None,
                 users=None, tickets=None, examples=None, description=None, parent=None,
                 xfails=None, xflags=None, only=None, skip=None,
                 start=None, end=None, args=None, id=None, node=None, map=None, context=None,
                 _frame=None, _run=True):

        self.lock = threading.Lock()
        self._run = _run

        cli_args = {}
        if current() is None:
            if top() is not None:
                raise RuntimeError("only one top level test is allowed")
            top(self)
            # flag to indicate if main test called init
            self._init= False
            frame = get(_frame, inspect.currentframe().f_back.f_back.f_back)
            if main(frame):
                cli_args, xflags, only, skip, start, end, name, tags, attributes = self.parse_cli_args(
                    xflags, only, skip, start, end, name, tags, attributes)

        self.name = name
        if self.name is None:
            raise TypeError("name must be specified")
        self.child_count = 0
        self.start_time = time.time()
        self.parent = parent
        self.id = get(id, [settings.test_id])
        self.node = get(node, self.node)
        self.map = get(map, self.map)
        self.type = get(type, self.type)
        self.subtype = get(subtype, self.subtype)
        self.context = get(context, current().context if current() and self.type < TestType.Test else (TestContext(current().context if current() else None)))
        self.tags = tags
        self.requirements = get(requirements, self.requirements)
        self.attributes = get(attributes, self.attributes)
        self.users = get(users, self.users)
        self.tickets = get(tickets, self.tickets)
        self.description = get(description, self.description)
        self.examples = get(examples, get(self.examples, ExamplesTable()))
        self.args = get(args, {})
        self.args.update({k:v for k, v in cli_args.items() if not k.startswith("_")})
        self._process_args()
        self.result = Null(self.name)
        if flags is not None:
            self.flags = Flags(flags)
        self.cflags = Flags(cflags) | (self.flags & CFLAGS)
        self.uid = get(uid, self.uid)
        self.xfails = get(xfails, {})
        self.xflags = get(xflags, {})
        self.only = get(only, [])
        self.skip = get(skip, [])
        self.start = get(start, None)
        self.end = get(end, None)
        self.caller_test = None

    @classmethod
    def make_name(cls, name, parent=None):
        """Make full name.

        :param name: name
        :param parent: parent name
        """
        name = name % {"name": cls.name} if name is not None else cls.name
        if name is None:
            raise TypeError("name must be specified")
        # '/' is not allowed just like in Unix file names
        # so convert any '/' to U+2215 division slash
        name = name.replace(name_sep, "\u2215")
        return join(get(parent, name_sep), name)

    @classmethod
    def make_tags(cls, tags):
        return set(get(tags, cls.tags))

    def _process_args(self):
        """Process arguments by converting
        them into a dictionary of
        "name:Argument" pairs
        """
        args = []
        try:
            for name in dict(self.args):
                value = self.args.get(name)
                if not isinstance(value, Argument):
                    value = Argument(name=name, value=value)
                args.append(value)

            self.args = {}

            for arg in args:
                if not isinstance(arg, Argument):
                    raise ValueError(f"not an argument {arg}")
                self.args[arg.name] = arg
        except ArgumentError:
            raise
        except Exception as e:
            raise ArgumentError(str(e))

    def __enter__(self):
        self.io = TestIO(self)
        if top() is self:
            self.io.output.protocol()
            self.io.output.version()
        self.io.output.test_message()

        if self.flags & PAUSE_BEFORE:
            pause()

        self.caller_test = current()
        current(self)

        if self.flags & SKIP:
            raise ResultException(Skip(self.name, "skip flag set"))
        else:
            if top() is self:
                self._init = init()
            if self._run:
                self.run(**{name: arg.value for name, arg in self.args.items()})
            return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        if top() is self and not self._init:
            return False

        def process_exception(exception_type, exception_value, exception_traceback):
            if isinstance(exception_value, ResultException):
                self.result = self.result(exception_value.result)
            elif isinstance(exception_value, AssertionError):
                exception(test=self)
                self.result = self.result(Fail(self.name, str(exception_value)))
            else:
                exception(test=self)
                result = Error(self.name,
                    "unexpected %s: %s" % (exception_type.__name__, str(exception_value)))
                self.result = self.result(result)
                if isinstance(exception_value, KeyboardInterrupt):
                    raise ResultException(result)

        try:
            if exception_value:
                process_exception(exception_type, exception_value, exception_traceback)
            else:
                if isinstance(self.result, Null):
                    self.result = self.result(OK(self.name))
        finally:
            try:
                if self.type >= TestType.Test:
                    if self.context._cleanups:
                        with Finally("I clean up"):
                            cleanup_exc_type, cleanup_exc_value, cleanup_exc_traceback = self.context._cleanup()
                        if not exception_value and cleanup_exc_value:
                            process_exception(cleanup_exc_type, cleanup_exc_value, cleanup_exc_traceback)
            finally:
                current(self.caller_test)
                previous(self)
                self._apply_xfails()
                self.io.output.result(self.result)
                self.io.close()

            if self.flags & PAUSE_AFTER:
                pause()

        return True

    def _apply_xfails(self):
        """Apply xfails to self.result.
        """
        for pattern, xouts in self.xfails.items():
            if match(self.name, pattern):
                for xout in xouts:
                    result, reason = xout
                    if isinstance(self.result, result):
                        self.result = self.result.xout(reason)

    def run(self, **args):
        pass

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

class _test(object):
    """Test definition.

    :param name: name of the test
    :param test: test class (optional), default: Test
    :param **kwargs: test class arguments
    """
    def __init__(self, name, **kwargs):
        current_thread = threading.current_thread()
        if getattr(current_thread, "_parent", None):
            parent_current = current(thread=current_thread._parent)
            parent_top = top(thread=current_thread._parent)
            parent_previous = previous(thread=current_thread._parent)
            if parent_current and not current():
                current(value=parent_current)
                top(value=parent_top)
                previous(value=parent_previous)

        parent = kwargs.pop("parent", None) or current()
        test = kwargs.pop("test", None)
        keep_type = kwargs.pop("keep_type", None)

        test = test if test is not None else TestBase

        if parent:
            name = test.make_name(name, parent.name)
            kwargs["parent"] = parent.name
            kwargs["id"] = parent.id + [parent.child_count]
            kwargs["cflags"] = parent.cflags
            # propagate xfails, xflags, only and skip that prefix match the name of the test
            kwargs["xfails"] = xfails({
                    k: v for k, v in parent.xfails.items() if match(name, k, prefix=True)
                }) or kwargs.get("xfails")
            kwargs["xflags"] = xflags({
                    k: v for k, v in parent.xflags.items() if match(name, k, prefix=True)
                }) or kwargs.get("xflags")
            kwargs["only"] = parent.only or kwargs.get("only")
            kwargs["skip"] = parent.skip or kwargs.get("skip")
            kwargs["start"] = parent.start or kwargs.get("start")
            kwargs["end"] = parent.end or kwargs.get("end")
            # handle parent test type propagation
            if keep_type is None:
                self._parent_type_propagation(parent, kwargs)
            with parent.lock:
                parent.child_count += 1
        else:
            name = test.make_name(name)
        tags = test.make_tags(kwargs.pop("tags", None))

        # anchor all patterns
        kwargs["xfails"] = xfails({
                absname(k, name if name else name_sep): v for k, v in (kwargs.get("xfails") or {}).items()
            }) or None
        kwargs["xflags"] = xflags({
                absname(k, name if name else name_sep): v for k, v in (kwargs.get("xflags") or {}).items()
            }) or None
        kwargs["only"] = [f.at(name if name else name_sep) for f in kwargs.get("only") or []] or None
        kwargs["skip"] = [f.at(name if name else name_sep) for f in kwargs.get("skip") or []] or None
        kwargs["start"] = kwargs.get("start").at(name if name else name_sep) if kwargs.get("start") else None
        kwargs["end"] = kwargs.get("end").at(name if name else name_sep) if kwargs.get("end") else None

        self.parent = parent
        self._apply_xflags(name, kwargs)
        self._apply_only(name, tags, kwargs)
        self._apply_skip(name, tags, kwargs)
        self._apply_start(name, tags, parent, kwargs)
        self._apply_end(name, tags, parent, kwargs)
        self._repeat = kwargs.pop("repeat", None)
        self._tags = tags
        self._kwargs = dict(kwargs)
        self.test = test(name, tags=tags, **kwargs)
        if getattr(self, "parent_type", None):
            self.test.parent_type = self.parent_type

    def _apply_end(self, name, tags, parent, kwargs):
        end = kwargs.get("end")
        if not end:
            return

        if end.match(name, tags):
            if parent:
                with parent.lock:
                    parent.end = None
                    parent.skip = [the("/*")]

    def _apply_start(self, name, tags, parent, kwargs):
        start = kwargs.get("start")
        if not start:
            return

        if not start.match(name, tags):
            kwargs["flags"] = Flags(kwargs.get("flags")) | SKIP
        else:
            kwargs["flags"] = Flags(kwargs.get("flags")) & ~SKIP
            if parent:
                with parent.lock:
                    parent.start = None

    def _apply_only(self, name, tags, kwargs):
        only = kwargs.get("only")
        if not only:
            return

        # only should not skip Given and Finally steps
        if kwargs.get("subtype") in (TestSubType.Given, TestSubType.Finally):
            only.append(the(join(name, "*")))

        found = False
        for item in only:
            if item.match(name, tags):
                found = True
                break

        if not found:
            kwargs["flags"] = Flags(kwargs.get("flags")) | SKIP
        else:
            kwargs["flags"] = Flags(kwargs.get("flags")) & ~SKIP

    def _apply_skip(self, name, tags, kwargs):
        skip = kwargs.get("skip")
        if not skip:
            return

        for item in skip:
            if item.match(name, tags, prefix=False):
                kwargs["flags"] = Flags(kwargs.get("flags")) | SKIP
                break

    def _apply_xflags(self, name, kwargs):
        xflags = kwargs.get("xflags")
        if not xflags:
            return
        for pattern, item in xflags.items():
            if match(name, pattern):
                set_flags, clear_flags = item
                kwargs["flags"] = (Flags(kwargs.get("flags")) & ~Flags(clear_flags)) | Flags(set_flags)

    def _parent_type_propagation(self, parent, kwargs):
        """Propagate parent test type if lower.

        :param parent: parent
        :param kwargs: test's kwargs
        """
        type = kwargs.pop("type", TestType.Test)
        subtype = kwargs.pop("subtype", TestSubType.Empty)

        parent_type = parent.type

        if parent_type == TestType.Iteration:
            parent_type = parent.parent_type

        if int(parent_type) < int(type):
            type = parent.type
            subtype = parent.subtype

        kwargs["subtype"] = subtype
        kwargs["type"] = type

    def __enter__(self):
        def dummy(*args, **kwargs):
            pass
        try:
            if self._repeat is not None:
                self._with_frame = inspect.currentframe().f_back
                self._with_block_start_lineno = self._with_frame.f_lineno
                self._with_source = inspect.getsourcelines(self._with_frame)
                self.trace = sys.gettrace()
                sys.settrace(dummy)
                sys._getframe(1).f_trace = functools.partial(self.__repeat__, None, None, None)
            else:
                return self.test.__enter__()
        except (KeyboardInterrupt, Exception):
            self.trace = sys.gettrace()
            sys.settrace(dummy)
            sys._getframe(1).f_trace = functools.partial(self.__nop__, *sys.exc_info())

    def __repeat__(self, *args):
        sys.settrace(self.trace)
        raise RepeatTestException()

    def __nop__(self, exc_type, exc_value, exc_tb, *args):
        sys.settrace(self.trace)
        raise exc_value.with_traceback(exc_tb)

    def __exit__(self, exception_type, exception_value, exception_traceback):
        frame = inspect.currentframe().f_back

        if isinstance(exception_value, RepeatTestException) and not frame.f_locals.get("_repeat") and top() != self.test:
            try:
                self.test.__enter__()
                self._with_block_end = frame.f_lasti
                self._with_block_end_lineno = self._with_frame.f_lineno
                lines, index = self._with_source
                index = max(1, index)
                source = textwrap.dedent("".join(
                    lines[(self._with_block_start_lineno - index)+1:(self._with_block_end_lineno - index) + 1]))
                code = compile(source, self._with_frame.f_code.co_filename, mode="exec")
                frame.f_locals["_repeat"] = True
                __kwargs = dict(self._kwargs)
                __kwargs.pop("name", None)
                __kwargs.pop("parent", None)
                __kwargs["type"] = TestType.Iteration
                __kwargs["subtype"] = TestSubType.Empty
                for i in range(self._repeat):
                    with Iteration(name=f"{i}", tags=self._tags, **__kwargs, parent_type=self.test.type):
                        exec(code, frame.f_globals, frame.f_locals)
                frame.f_locals.pop("_repeat")
            except:
                try:
                    test__exit__ = self.test.__exit__(*sys.exc_info())
                except(KeyboardInterrupt, Exception):
                    raise
            else:
                try:
                    test__exit__ = self.test.__exit__(None, None, None)
                except(KeyboardInterrupt, Exception):
                    raise
        else:
            try:
                test__exit__ = self.test.__exit__(exception_type, exception_value, exception_traceback)
            except (KeyboardInterrupt, Exception):
                raise

        # if test did not handle the exception in __exit__ then re-raise it
        if exception_value and not test__exit__:
            raise exception_value.with_traceback(exception_traceback)

        if not self.test.result:
            if not self.parent:
                sys.exit(1)

            if isinstance(self.test.result, Fail):
                result = Fail(self.parent.name, self.test.result.message)
            else:
                # convert Null into an Error
                result = Error(self.parent.name, self.test.result.message)

            if TE not in self.test.flags:
                raise ResultException(result)
            else:
                with self.parent.lock:
                    if isinstance(self.parent.result, Error):
                        pass
                    elif isinstance(self.test.result, Error) and ERROR_NOT_COUNTED not in self.test.flags:
                        self.parent.result = result
                    elif isinstance(self.test.result, Null) and NULL_NOT_COUNTED not in self.test.flags:
                        self.parent.result = result
                    elif isinstance(self.parent.result, Fail):
                        pass
                    elif isinstance(self.test.result, Fail) and FAIL_NOT_COUNTED not in self.test.flags:
                        self.parent.result = result
                    else:
                        pass
        return True

class Module(_test):
    """Module definition."""
    def __init__(self, name, **kwargs):
        kwargs["type"] = TestType.Module
        return super(Module, self).__init__(name, **kwargs)

class Suite(_test):
    """Suite definition."""
    def __init__(self, name, **kwargs):
        kwargs["type"] = TestType.Suite
        return super(Suite, self).__init__(name, **kwargs)

class Test(_test):
    """Test definition."""
    def __init__(self, name, **kwargs):
        kwargs["type"] = TestType.Test
        return super(Test, self).__init__(name, **kwargs)

class Iteration(_test):
    """Test iteration definition."""
    def __init__(self, name, **kwargs):
        kwargs["type"] = TestType.Iteration
        self.parent_type = kwargs.pop("parent_type", TestType.Test)
        return super(Iteration, self).__init__(name, **kwargs)

class Step(_test):
    """Step definition."""
    def __init__(self, name, **kwargs):
        kwargs["type"] = TestType.Step
        return super(Step, self).__init__(name, **kwargs)

# support for BDD
class Feature(Suite):
    def __init__(self, name, **kwargs):
        kwargs["subtype"] = TestSubType.Feature
        kwargs["_frame"] = kwargs.pop("_frame", inspect.currentframe().f_back )
        return super(Feature, self).__init__(name, **kwargs)

class Scenario(Test):
    def __init__(self, name, **kwargs):
        kwargs["subtype"] = TestSubType.Scenario
        kwargs["_frame"] = kwargs.pop("_frame", inspect.currentframe().f_back )
        return super(Scenario, self).__init__(name, **kwargs)

class _background(Test):
    def __init__(self, name, **kwargs):
        kwargs["subtype"] = TestSubType.Background
        kwargs["_frame"] = kwargs.pop("_frame", inspect.currentframe().f_back.f_back)
        return super(_background, self).__init__(name, **kwargs)

class Steps(ExitStack):
    def __init__(self, *args, **kwargs):
        self.values = []
        super(Steps, self).__init__(*args, **kwargs)

    def __call__(self, ctx):
        step = self.enter_context(ctx)
        self.values.append(step)
        return step

@contextmanager
def Background(name, **kwargs):
    with _background(name, **kwargs) as bg:
        with ExitStack() as stack:
            bg.stack = stack
            yield bg

def Given(step, **kwargs):
    kwargs["subtype"] = TestSubType.Given
    kwargs["_frame"] = kwargs.pop("_frame", inspect.currentframe().f_back )
    if isinstance(step, TestStep):
        return step(**kwargs)
    else:
        return Step(step, **kwargs)

def When(step, **kwargs):
    kwargs["subtype"] = TestSubType.When
    kwargs["_frame"] = kwargs.pop("_frame", inspect.currentframe().f_back )
    if isinstance(step, TestStep):
        return step(**kwargs)
    else:
        return Step(step, **kwargs)

def Then(step, **kwargs):
    kwargs["subtype"] = TestSubType.Then
    kwargs["_frame"] = kwargs.pop("_frame", inspect.currentframe().f_back )
    if isinstance(step, TestStep):
        return step(**kwargs)
    else:
        return Step(step, **kwargs)

def And(step, **kwargs):
    kwargs["subtype"] = TestSubType.And
    kwargs["_frame"] = kwargs.pop("_frame", inspect.currentframe().f_back )
    if isinstance(step, TestStep):
        return step(**kwargs)
    else:
        return Step(step, **kwargs)

def But(step, **kwargs):
    kwargs["subtype"] = TestSubType.But
    kwargs["_frame"] = kwargs.pop("_frame", inspect.currentframe().f_back )
    if isinstance(step, TestStep):
        return step(**kwargs)
    else:
        return Step(step, **kwargs)

def By(step, **kwargs):
    kwargs["subtype"] = TestSubType.By
    kwargs["_frame"] = kwargs.pop("_frame", inspect.currentframe().f_back )
    if isinstance(step, TestStep):
        return step(**kwargs)
    else:
        return Step(step, **kwargs)

def Finally(step, **kwargs):
    kwargs["subtype"] = TestSubType.Finally
    kwargs["_frame"] = kwargs.pop("_frame", inspect.currentframe().f_back )
    if isinstance(step, TestStep):
        return step(**kwargs)
    else:
        return Step(step, **kwargs)

class NullStep():
    def __enter__(self):
        return None

    def __exit__(self, *args, **kwargs):
        return False

# decorators
class _testdecorator(object):
    type = Test
    def __init__(self, func):
        func.name = getattr(func, "name", func.__name__.replace("_", " "))
        func.description = getattr(func, "description", func.__doc__)
        self.func = func
        functools.update_wrapper(self, func)

    def __call__(self, **kwargs):
        frame = kwargs.pop("_frame", inspect.currentframe().f_back)
        _kwargs = dict(vars(self.func))
        _name = kwargs.pop("name", None)
        _repeat = kwargs.pop("repeat", None)
        if kwargs.get("args") is None:
            # use function signature to get default argument values
            # and set them as args
            signature = inspect.signature(self.func)
            kwargs["args"] = { p.name:p.default for p in signature.parameters.values() if p.default != inspect.Parameter.empty }
        if _name is not None:
            kwargs["name"] = _name % (_kwargs)
        _kwargs.update(kwargs)
        # handle repeats
        if _repeat is not None:
            with self.type(**_kwargs, _frame=frame, _run=False) as parent_test:
                __kwargs = dict(_kwargs)
                __kwargs.pop("name")
                __kwargs["type"] = TestType.Iteration
                __kwargs["subtype"] = TestSubType.Empty
                for i in range(_repeat):
                    with Iteration(name=f"{i}", parent_type=parent_test.type, **__kwargs) as test:
                        self.func(**{name: arg.value for name, arg in test.args.items()})
            return parent_test
        else:
            with self.type(**_kwargs, _frame=frame) as test:
                r = self.func(**{name: arg.value for name, arg in test.args.items()})
                def run_generator():
                    return next(r)
                if inspect.isgenerator(r):
                    run_generator()
                    test.context.cleanup(run_generator)
            return test

class TestStep(_testdecorator):
    type = Step

class TestCase(_testdecorator):
    type = Test

class TestScenario(TestCase):
    type = Scenario

class TestSuite(_testdecorator):
    type = Suite

class TestFeature(TestSuite):
    type = Feature

class TestModule(_testdecorator):
    type = Module

class TestClass(object):
    def __init__(self, test):
        self.test = test

    def __call__(self, func):
        func.test = self.test
        return func

class Name(object):
    def __init__(self, name):
        self.name = name

    def __call__(self, func):
        func.name = self.name
        return func

class Description(object):
    def __init__(self, description):
        self.description = description

    def __call__(self, func):
        func.description = self.description
        return func

class Examples(object):
    def __init__(self, header, rows, row_format=None):
        self.examples = ExamplesTable(header, rows=rows, row_format=row_format)

    def __call__(self, func):
        func.examples = self.examples
        return func

class Attributes(object):
    def __init__(self, *attributes):
        self.attributes = attributes

    def __call__(self, func):
        func.attributes = self.attributes
        return func

class Requirements(object):
    def __init__(self, *requirements):
        self.requirements = requirements

    def __call__(self, func):
        func.requirements = self.requirements
        return func

class Tags(object):
    def __init__(self, *tags):
        self.tags = tags

    def __call__(self, func):
        func.tags = self.tags
        return func

class Uid(object):
    def __init__(self, uid):
        self.uid = uid

    def __call__(self, func):
        func.uid = self.uid
        return func

class Users(object):
    def __init__(self, *users):
        self.users = users

    def __call__(self, func):
        func.users = self.users
        return func

class Tickets(object):
    def __init__(self, *tickets):
        self.tickets = tickets

    def __call__(self, func):
        func.tickets = self.tickets
        return func

def run(comment=None, test=None, **kwargs):
    """Run a test.

    :param comment: comment
    :param test: test
    :param **kwargs: other test arguments
    """
    if test is None:
        raise TypeError("run() test argument must be specified")
    if inspect.isclass(test) and issubclass(test, TestBase):
        test = test
    elif issubclass(type(test), _testdecorator):
        return test(**kwargs, _frame=inspect.currentframe().f_back)
    elif inspect.isfunction(test):
        return test(**kwargs)
    elif inspect.ismethod(test):
        return test(**kwargs)
    else:
        raise TypeError(f"invalid test type '{type(test)}'")

    _frame = inspect.currentframe().f_back
    _repeat = kwargs.pop("repeat", None)
    if _repeat is not None:
        with globals()["Test"](test=test, name=kwargs.pop("name", None), **kwargs,
                               _frame=_frame, _run=False) as parent_test:
            _kwargs = dict(kwargs)
            _kwargs["type"] = TestType.Iteration
            _kwargs["subtype"] = TestSubType.Empty
            for i in range(_repeat):
                with Iteration(test=test, name=f"{i}", **kwargs, _frame=_frame, parent_type=parent_test.type):
                    pass
        return parent_test.result
    else:
        with globals()["Test"](test=test, name=kwargs.pop("name", None), **kwargs, _frame=frame) as test:
            pass
        return test.result
