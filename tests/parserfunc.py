#!/usr/bin/python3
from testflows.core import *
from testflows.asserts import error


def mytype(v):
    return "hello"


def argparser(parser):
    def func(args, kwargs):
        assert args["build"] == "hello", error()
        args["build"] = "hello there"

    parser.add_argument("--build", type=mytype, default=None)
    parser.set_defaults(func=func)

    return config.Schema({config.Optional("build"): str})


@TestModule
@Name("user defined argument parser function")
@Attributes(("my attr build", "not defined"))
@ArgumentParser(argparser)
def regression(self, build="not defined"):
    assert build == "hello there", error()


if main():
    regression()
