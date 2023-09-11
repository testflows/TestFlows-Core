from testflows.core import *


def add(a, b, c):
    note(f"{a} + {b} + {c}")


def boo():
    note("message from optional test")


@TestSketch
def my_sketch(self):
    note("Hello from pattern")

    for i in range(either(value=range(1, 2))):
        add(a=either(1, 2, i=i), b=either(3, 4, i=i), c=either(5, 6, i=i))

    for i in range(either(value=range(1, 4))):
        boo()

    with Step("my step"):
        if either():
            note("here")

    add(a=either(1, 2, 3, 4, 5, 6, 7, limit=1), b=2, c=2)


if main():
    with Feature("sketches"):
        Sketch(run=my_sketch, random=True)
