import asyncio
from testflows.core import *


@TestCase
async def my_test(self):
    note("my test")
    fail("foo")


@TestModule
@Name("regression")
async def module(self):
    """Check support for top level test to be async."""
    note("note")
    async with Test("foo"):
        note("test foo")
        async with Test("test1"):
            for i in range(10):
                async with Step(f"sleep #{i}"):
                    note("from test1")
                    await asyncio.sleep(1)
                    note("from test1 1")
            await Test(run=my_test)

    async with Test("test2"):
        pass


async def start():
    await Module(run=foo_module)


if main():
    with Module("main"):
        asyncio.run(module())
