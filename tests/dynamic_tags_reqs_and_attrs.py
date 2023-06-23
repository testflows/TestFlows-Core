from testflows.core import *
from testflows.asserts import error


@TestFeature
@Name("dynamic tags, requirements, and attributes")
def feature(self):
    """Check that we cat dynamically add
    tags, requirements, and attributes to a test.
    """

    def check():
        test = current()

        tag("A")
        assert "A" in test.tags, error()

        requirement("RQ.1", version="1.0")
        assert "RQ.1" in test.requirements, error()

        attribute("hello", "there")
        assert "hello" in test.attributes, error()

    with Step("step") as step:
        check()

    check()


if main():
    feature()
