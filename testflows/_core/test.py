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

from .exceptions import DummyTestException, ResultException, RepeatTestException
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
from .cli.arg.type import key_value as key_value_type, filter_type, repeat_type
from .cli.text import danger, warning
from .exceptions import exception as get_exception
from .filters import the

try:
    import testflows.database as database_module
except:
    database_module = None

class XFails(dict):
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

class XFlags(dict):
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
    examples = None
    name = None
    description = None
    node = None
    map = []
    flags = Flags()
    name_sep = "."
    type = TestType.Test
    subtype = None

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
        parser.add_argument("--skip", dest="_skip", metavar="pattern[,type]",
            help=("skip selected tests.\n"
                  "Where `pattern` is test name pattern, "
                  "and `type` is test type either {'test', 'suite', 'module'} "
                  "(default: 'test')"),
            type=filter_type, nargs="+", required=False)
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
            choices=["slick", "nice", "quiet", "short", "dots", "raw"], default="nice",
            help="""stdout output format, choices are: ['slick','nice','short','dots','quiet','raw'],
                default: 'nice'""")
        parser.add_argument("-l", "--log", dest="_log", metavar="file", type=str,
            help="path to the log file where test output will be stored, default: uses temporary log file")
        parser.add_argument("--show-skipped", dest="_show_skipped", action="store_true",
            help="show skipped tests, default: False", default=False)
        parser.add_argument("--repeat", dest="_repeat",
            help=("number of times to repeat a test until it either passes or fails.\n"
                  "Where `number` is a number times to repeat the test, "
                  "`pattern` is a test name pattern (default: '*'), "
                  "`until` repeat until condition either {'pass', 'fail'} (default: 'pass'), "
                  "and `type` is test type either {'test', 'suite', 'module'} "
                  "(default: 'test')"),
            type=repeat_type, metavar="number[,pattern[,until[,type]]]", nargs="+", required=False)
        if database_module:
            database_module.argparser(parser)
        return parser

    def parse_cli_args(self, xflags=None, only=None, skip=None, start=None, end=None,
            name=None, tags=None, attributes=None, repeat=None):
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

            if args.get("_database"):
                settings.database = args.pop("_database")

            if args.get("_show_skipped"):
                settings.show_skipped = True
                args.pop("_show_skipped")

            if args.get("_pause_before"):
                if not xflags:
                    xflags = globals()["XFlags"]()
                for pattern in args.get("_pause_before"):
                    pattern = absname(pattern, name)
                    xflags[pattern] = xflags.get(pattern, [0, 0])
                    xflags[pattern][0] |= PAUSE_BEFORE
                args.pop("_pause_before")

            if args.get("_pause_after"):
                if not xflags:
                    xflags = globals()["XFlags"]()
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
                skip = {TestType.Test: [], TestType.Suite: [], TestType.Module: []}
                for item in args.pop("_skip"):
                    skip[item.type].append(item)

            if args.get("_start"):
                start = the(args.get("_start")[0]).at(name)
                args.pop("_start")

            if args.get("_end"):
                end = the(args.get("_end")[0]).at(name)
                args.pop("_end")

            if args.get("_tags"):
                tags = {value for value in args.pop("_tags")}

            if args.get("_attrs"):
                attributes = [Attribute(item.key, item.value) for item in args.pop("_attrs")]

            if args.get("_repeat"):
                repeat = {TestType.Test: [], TestType.Suite: [], TestType.Module: []}
                for item in args.pop("_repeat"):
                    repeat[item.type].append(item)

        except (ExitException, KeyboardInterrupt, Exception) as exc:
            sys.stderr.write(warning(get_exception(), eol='\n'))
            sys.stderr.write(danger("error: " + str(exc).strip()))
            if isinstance(exc, ExitException):
                sys.exit(exc.exitcode)
            else:
                sys.exit(1)

        return args, xflags, only, skip, start, end, name, tags, attributes, repeat

    def __init__(self, name=None, flags=None, cflags=None, type=None, subtype=None,
                 uid=None, tags=None, attributes=None, requirements=None,
                 examples=None, description=None, parent=None,
                 xfails=None, xflags=None, only=None, skip=None,
                 start=None, end=None, args=None, id=None, node=None, map=None, context=None,
                 repeat=None, _frame=None):

        self.lock = threading.Lock()

        cli_args = {}
        if current() is None:
            if top() is not None:
                raise RuntimeError("only one top level test is allowed")
            top(self)
            # flag to indicate if main test called init
            self._init= False
            frame = get(_frame, inspect.currentframe().f_back.f_back.f_back)
            if main(frame):
                cli_args, xflags, only, skip, start, end, name, tags, attributes, repeat = self.parse_cli_args(
                    xflags, only, skip, start, end, name, tags, attributes, repeat)

        self.name = name
        if self.name is None:
            raise TypeError("name must be specified")
        self.child_count = 0
        self.start_time = time.time()
        self.parent = parent
        self.id = get(id, [settings.test_id])
        self.node = get(node, self.node)
        self.map = get(map, list(self.map))
        self.type = get(type, self.type)
        self.subtype = get(subtype, self.subtype)
        self.context = get(context, current().context if current() and self.type < TestType.Iteration else (Context(current().context if current() else None)))
        self.tags = tags
        self.requirements = {r.name: r for r in get(requirements, list(self.requirements))}
        self.attributes =  {a.name: a for a in get(attributes, list(self.attributes))}
        self.attributes.update({k: Attribute(k, v) for k, v in cli_args.items() if not k.startswith("_")})
        self.args = {k: Argument(k,v) for k,v in get(args, {}).items()}
        self.description = get(description, self.description)
        self.examples = get(examples, get(self.examples, ExamplesTable()))
        self.result = Null(test=self.name)
        if flags is not None:
            self.flags = Flags(flags)
        self.cflags = Flags(cflags) | (self.flags & CFLAGS)
        self.uid = get(uid, self.uid)
        self.xfails = get(xfails, {})
        self.xflags = get(xflags, {})
        self.only = get(only, [])
        self.skip = get(skip, None)
        self.start = get(start, None)
        self.end = get(end, None)
        self.repeat = get(repeat, None)
        self.caller_test = None

    @classmethod
    def make_name(cls, name, parent=None, args=None):
        """Make full name.

        :param name: name
        :param parent: parent name
        :param args: arguments to the test
        """
        if args is None:
            args = dict()
        name = name.format(**{"$name": cls.name}, **args) if name is not None else cls.name
        if name is None:
            raise TypeError("name must be specified")
        # '/' is not allowed just like in Unix file names
        # so convert any '/' to U+2215 division slash
        name = name.replace(name_sep, "\u2215")
        return join(get(parent, name_sep), name)

    @classmethod
    def make_tags(cls, tags):
        return set(get(tags, cls.tags))

    def _enter(self):
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
            raise Skip("skip flag set", test=self.name)
        else:
            if top() is self:
                self._init = init()
            return self

    def _exit(self, exc_type, exc_value, exc_traceback):
        if top() is self and not self._init:
            return False

        def process_exception(exc_type, exc_value, exc_traceback):
            if isinstance(exc_value, ResultException):
                self.result = self.result(exc_value)
            elif isinstance(exc_value, AssertionError):
                exception(exc_type, exc_value, exc_traceback, test=self)
                self.result = self.result(Fail(str(exc_value), test=self.name))
            else:
                exception(exc_type, exc_value, exc_traceback, test=self)
                result = Error("unexpected %s: %s" % (exc_type.__name__, str(exc_value)), test=self.name)
                self.result = self.result(result)
                if isinstance(exc_value, KeyboardInterrupt):
                    raise result

        try:
            if exc_value is not None:
                process_exception(exc_type, exc_value, exc_traceback)
            else:
                if isinstance(self.result, Null):
                    self.result = self.result(OK(test=self.name))
        finally:
            try:
                if self.type >= TestType.Test:
                    if self.context._cleanups:
                        with Finally("I clean up"):
                            cleanup_exc_type, cleanup_exc_value, cleanup_exc_traceback = self.context._cleanup()
                        if not exc_value and cleanup_exc_value:
                            process_exception(cleanup_exc_type, cleanup_exc_value, cleanup_exc_traceback)
            finally:
                current(self.caller_test)
                previous(self)
                self._apply_xfails()
                self.io.output.result(self.result)
                if top() is self:
                    self.io.output.stop()
                    self.io.close(final=True)
                else:
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

class TestDefinition(object):
    """Test definition.

    :param name: name of the test
    :param **kwargs: test class arguments
    """
    type = TestType.Test

    def __new__(cls, name=None, **kwargs):
        run = kwargs.pop("run", None)
        test = kwargs.pop("test", None)

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
            else:
                kwargs["test"] = run
            return cls.__create__(**kwargs)()

        if test:
            if isinstance(test, TestDecorator):
                kwargs = inherit_kwargs(**test.func.kwargs)
                kwargs["test"] = test
            elif isinstance(test, TestDefinition):
                kwargs = inherit_kwargs(**test.kwargs, **({"name": test.name} if test.name is not None else {}))
            else:
                kwargs["test"] = test

        return cls.__create__(**kwargs)

    @classmethod
    def __create__(cls,  **kwargs):
        self = super(TestDefinition, cls).__new__(cls)
        self.name = kwargs.pop("name", None)
        self.test = None
        self.parent = None
        self.kwargs = kwargs
        self.tags = None
        self.repeat = None
        self.repeatable_func = None
        return self

    def __call__(self, **args):
        test = self.kwargs.get("test", None)
        self.kwargs["args"] = self.kwargs.get("args", {})
        self.kwargs["args"].update(args)

        if test and isinstance(test, TestDecorator):
            self.repeatable_func = test
            with self as _test:
                test(**args)
            return _test
        else:
            with self as _test:
                pass
            return _test

    def __enter__(self):
        def dummy(*args, **kwargs):
            pass
        try:
            self._set_current_top_previous()

            kwargs = self.kwargs
            keep_type = kwargs.pop("keep_type", None)

            self.parent = kwargs.pop("parent", None) or current()
            parent = self.parent
            repeat = None

            test = kwargs.pop("test", None)
            if test and isinstance(test, TestDecorator):
                test = test.func.kwargs.get("test", None)
            test = test if test is not None else TestBase
            if not issubclass(test, TestBase):
                raise TypeError(f"{test} must be subclass of TestBase")
            name = test.make_name(self.name, parent.name if parent else None, kwargs.get("args", None))

            if parent:
                kwargs["parent"] = parent.name
                kwargs["id"] = parent.id + [parent.child_count]
                kwargs["cflags"] = parent.cflags
                # propagate xfails, xflags, only and skip that prefix match the name of the test
                kwargs["xfails"] = XFails({
                    k: v for k, v in parent.xfails.items() if match(name, k, prefix=True)
                }) or kwargs.get("xfails")
                kwargs["xflags"] = XFlags({
                    k: v for k, v in parent.xflags.items() if match(name, k, prefix=True)
                }) or kwargs.get("xflags")
                kwargs["only"] = parent.only or kwargs.get("only")
                kwargs["skip"] = parent.skip or kwargs.get("skip")
                kwargs["start"] = parent.start or kwargs.get("start")
                kwargs["end"] = parent.end or kwargs.get("end")
                # propagate repeat
                if parent.repeat and parent.type > TestType.Test:
                    if self.type is TestType.Module:
                        repeat = parent.repeat
                    elif self.type is TestType.Suite:
                        repeat = {
                            TestType.Module:[],
                            TestType.Suite: parent.repeat[TestType.Suite],
                            TestType.Test: parent.repeat[TestType.Test]
                        }
                    elif self.type is TestType.Test:
                        repeat = {
                            TestType.Module: [],
                            TestType.Suite: [],
                            TestType.Test: parent.repeat[TestType.Test]
                        }
                # handle parent test type propagation
                if keep_type is None:
                    self._parent_type_propagation(parent, kwargs)
                with parent.lock:
                    parent.child_count += 1

            tags = test.make_tags(kwargs.pop("tags", None))

            # anchor all patterns
            kwargs["xfails"] = XFails({
                absname(k, name if name else name_sep): v for k, v in (kwargs.get("xfails") or {}).items()
            }) or None
            kwargs["xflags"] = XFlags({
                absname(k, name if name else name_sep): v for k, v in (kwargs.get("xflags") or {}).items()
            }) or None
            kwargs["only"] = [f.at(name if name else name_sep) for f in kwargs.get("only") or []] or None
            kwargs["start"] = kwargs.get("start").at(name if name else name_sep) if kwargs.get("start") else None
            kwargs["end"] = kwargs.get("end").at(name if name else name_sep) if kwargs.get("end") else None

            self._apply_xflags(name, kwargs)
            self._apply_only(name, tags, kwargs)
            self._apply_skip(name, tags, parent, kwargs)
            self._apply_start(name, tags, parent, kwargs)
            self._apply_end(name, tags, parent, kwargs)
            self.tags = tags
            self.repeat = repeat

            self.test = test(name, tags=tags, repeat=repeat, **kwargs)
            if getattr(self, "parent_type", None):
                self.test.parent_type = self.parent_type

            if repeat is not None:
                count = self._apply_repeat(name, tags, parent, repeat)
                if count:
                    self.trace = sys.gettrace()
                    sys.settrace(dummy)
                    sys._getframe(1).f_trace = functools.partial(self.__repeat__, count, None, None, None)
                    return
            return self.test._enter()

        except (KeyboardInterrupt, Exception):
            self.trace = sys.gettrace()
            sys.settrace(dummy)
            sys._getframe(1).f_trace = functools.partial(self.__nop__, *sys.exc_info())

    def _set_current_top_previous(self):
        """Set current, top and previous
        using the parent thread if needed.
        """
        current_thread = threading.current_thread()
        if getattr(current_thread, "_parent", None):
            parent_current = current(thread=current_thread._parent)
            parent_top = top(thread=current_thread._parent)
            parent_previous = previous(thread=current_thread._parent)
            if parent_current and not current():
                current(value=parent_current)
                top(value=parent_top)
                previous(value=parent_previous)

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

    def _apply_repeat(self, name, tags, parent, repeat):
        if not repeat:
            return False

        items = repeat.get(self.type, [])
        for item in items:
            if the(item.pattern).at(parent.name).match(name, tags, prefix=False):
                return item.number

        return False

    def _apply_only(self, name, tags, kwargs):
        only = kwargs.get("only")
        if not only:
            return

        # only should not skip Given and Finally steps
        if kwargs.get("subtype") in (TestSubType.Background, TestSubType.Given, TestSubType.Finally):
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

    def _apply_skip(self, name, tags, parent, kwargs):
        skip = kwargs.get("skip")
        if not skip:
            return

        items = skip.get(self.type, [])
        for item in items:
            if the(item.pattern).at(parent.name).match(name, tags, prefix=False):
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
        subtype = kwargs.pop("subtype", None)

        parent_type = parent.type

        if parent_type == TestType.Iteration:
            parent_type = parent.parent_type

        if int(parent_type) < int(type):
            type = parent.type
            subtype = parent.subtype

        kwargs["subtype"] = subtype
        kwargs["type"] = type

    def __repeat__(self, count=None, *args):
        sys.settrace(self.trace)
        raise RepeatTestException(count)

    def __nop__(self, exc_type, exc_value, exc_tb, *args):
        sys.settrace(self.trace)
        raise exc_value.with_traceback(exc_tb)

    def __exit__(self, exception_type, exception_value, exception_traceback):
        frame = inspect.currentframe().f_back

        if self.test is None:
            return

        if isinstance(exception_value, RepeatTestException):
            try:
                count = exception_value.count
                self.test._enter()
                if self.repeatable_func is None:
                    raise Error("not repeatable")
                __kwargs = dict(self.kwargs)
                __kwargs.pop("name", None)
                __kwargs.pop("parent", None)
                __kwargs["type"] = TestType.Iteration
                __args = __kwargs.pop("args", {})
                for i in range(count):
                    with Iteration(name=f"{i}", tags=self.tags, **__kwargs, parent_type=self.test.type):
                        self.repeatable_func(**__args)
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
                test__exit__ = self.test._exit(exception_type, exception_value, exception_traceback)
            except (KeyboardInterrupt, Exception):
                raise

        # if test did not handle the exception in _exit then re-raise it
        if exception_value and not test__exit__:
            raise exception_value.with_traceback(exception_traceback)

        if not self.test.result:
            if not self.parent:
                sys.exit(1)

            if isinstance(self.test.result, Fail):
                result = Fail(test=self.parent.name, message=self.test.result.message)
            else:
                # convert Null into an Error
                result = Error(test=self.parent.name, message=self.test.result.message)

            if TE not in self.test.flags:
                raise result
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

class Module(TestDefinition):
    """Module definition."""
    type = TestType.Module

    def __new__(cls, name=None, **kwargs):
        kwargs["type"] = TestType.Module
        kwargs["_frame"] = kwargs.pop("_frame", inspect.currentframe().f_back)
        return super(Module, cls).__new__(cls, name, **kwargs)

class Suite(TestDefinition):
    """Suite definition."""
    type = TestType.Suite

    def __new__(cls, name=None, **kwargs):
        kwargs["type"] = TestType.Suite
        kwargs["_frame"] = kwargs.pop("_frame", inspect.currentframe().f_back)
        return super(Suite, cls).__new__(cls, name, **kwargs)

class Test(TestDefinition):
    """Test definition."""
    type = TestType.Test

    def __new__(cls, name=None, **kwargs):
        kwargs["type"] = TestType.Test
        kwargs["_frame"] = kwargs.pop("_frame", inspect.currentframe().f_back)
        return super(Test, cls).__new__(cls, name, **kwargs)

class Iteration(TestDefinition):
    """Test iteration definition."""
    type = TestType.Iteration

    def __new__(cls, name, **kwargs):
        kwargs["type"] = TestType.Iteration
        parent_type = kwargs.pop("parent_type", TestType.Test)
        self = super(Iteration, cls).__new__(cls, name, **kwargs)
        self.parent_type = parent_type
        return self

class Step(TestDefinition):
    """Step definition."""
    type = TestType.Step
    subtype = None

    def __new__(cls, name=None, **kwargs):
        kwargs["type"] = kwargs.pop("type", cls.type)
        kwargs["subtype"] = kwargs.pop("subtype", cls.subtype)
        kwargs["_frame"] = kwargs.pop("_frame", inspect.currentframe().f_back)
        return super(Step, cls).__new__(cls, name, **kwargs)

# support for BDD
class Feature(Suite):
    def __new__(cls, name, **kwargs):
        kwargs["subtype"] = TestSubType.Feature
        kwargs["_frame"] = kwargs.pop("_frame", inspect.currentframe().f_back )
        return super(Feature, cls).__new__(cls, name, **kwargs)

class Scenario(Test):
    def __new__(cls, name=None, **kwargs):
        kwargs["subtype"] = TestSubType.Scenario
        kwargs["_frame"] = kwargs.pop("_frame", inspect.currentframe().f_back )
        return super(Scenario, cls).__new__(cls, name, **kwargs)

class BackgroundTest(TestBase):
    def __init__(self, *args, **kwargs):
        self.contexts = []
        super(BackgroundTest, self).__init__(*args, **kwargs)

    def _enter(self):
        self.stack = ExitStack().__enter__()
        self.context.cleanup(self.stack.__exit__, None, None, None)
        return super(BackgroundTest, self)._enter()

    def append(self, ctx_manager):
        ctx = self.stack.enter_context(ctx_manager)
        self.contexts.append(ctx)
        return ctx

    def __iter__(self):
        return iter(self.contexts)

class Background(Step):
    subtype = TestSubType.Background

    def __new__(cls, name=None, **kwargs):
        kwargs["test"] = kwargs.pop("test", BackgroundTest)
        return super(Background, cls).__new__(cls, name, **kwargs)

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

class NullStep():
    def __enter__(self):
        return None

    def __exit__(self, *args, **kwargs):
        return False

# decorators
class TestDecorator(object):
    type = Test

    def __init__(self, func):
        self.func = func
        functools.update_wrapper(self, self.func)

        self.func.type = self.type.type
        self.func._frame = inspect.currentframe().f_back
        self.func.name = getattr(self.func, "name", self.func.__name__.replace("_", " "))
        self.func.description = getattr(self.func, "description", self.func.__doc__)

        kwargs = dict(vars(self.func))
        signature = inspect.signature(self.func)
        kwargs["args"] = {p.name: p.default for p in signature.parameters.values() if p.default != inspect.Parameter.empty}
        
        self.func.kwargs = kwargs

    def __call__(self, **args):
        return self.__run__(**args)

    def __run__(self, **args):
        test = current()

        def run(test):
            r = self.func(test, **args)
            def run_generator(r):
                return next(r)
            if inspect.isgenerator(r):
                res = run_generator(r)
                test.context.cleanup(run_generator, r)
                r = res
            return r

        if test is None or (test is not None and test.type > self.type.type):
            kwargs = dict(self.func.kwargs)
            kwargs["args"] = dict(kwargs.get("args", {}))
            kwargs["args"].update(args)
            return self.type(**kwargs, run=self)
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

        if args:
            raise TypeError(f"{self.func.__name__}() takes only named arguments")

        return self.__run__(**kwargs)

class TestCase(TestDecorator):
    type = Test

class TestScenario(TestCase):
    type = Scenario

class TestSuite(TestDecorator):
    type = Suite

class TestFeature(TestSuite):
    type = Feature

class TestModule(TestDecorator):
    type = Module

class TestBackground(TestDecorator):
    type = Background

    def __init__(self, func):
        func.test = getattr(func, "test", BackgroundTest)
        if not issubclass(func.test, BackgroundTest):
            raise TypeError(f"{func.test} must be subclass of BackgroundTest")
        return super(TestBackground, self).__init__(func)

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

def tests(module=None, *types, frame=None):
    if module is None:
        if frame is None:
            frame = inspect.currentframe().f_back
        module = sys.modules[frame.f_globals["__name__"]]
    if not types:
        types = (TestDecorator,)

    def is_type(member):
        return isinstance(member, types)

    return [test for name, test in inspect.getmembers(module, is_type)]

def cases(module=None, *types, frame=None):
    if not types:
        types = (TestCase,)
    if frame is None:
        frame = inspect.currentframe().f_back
    return tests(module, *types, frame=frame)

def suites(module=None, *types, frame=None):
    if not types:
        types = (TestSuite,)
    if frame is None:
        frame = inspect.currentframe().f_back
    return tests(module, *types, frame=frame)

def scenarios(module=None, *types, frame=None):
    if not types:
        types = (TestScenario,)
    if frame is None:
        frame = inspect.currentframe().f_back
    return tests(module, *types, frame=frame)

def features(module=None, *types, frame=None):
    if not types:
        types = (TestFeatures,)
    if frame is None:
        frame = inspect.currentframe().f_back
    return tests(module, *types, frame=frame)


def steps(module=None, *types, frame=None):
    if not types:
        types = (TestStep,)
    if frame is None:
        frame = inspect.currentframe().f_back
    return tests(module, *types, frame=frame)
