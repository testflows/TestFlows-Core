from testflows.core import *
from testflows.asserts import raises
from testflows.connect import Shell


@TestScenario
def check_filtering(self, secret):
    with When("in note, debug, trace"):
        note(secret.value)
        debug(secret.value)
        trace(secret.value)

    with When("in terminal"):
        with Shell() as bash:
            bash(f'export SECRET="{secret.value}"')


@TestModule
def feature(self):
    """Test basic usage of secret."""
    secret = Secret("secret")("hello there")

    with When("creating secret"):
        Secret("my_secret")("my secret value")

    with When("creating secret with invalid name"):
        with raises(ValueError):
            Secret("my secret")("my secret value")

    with When("secret object"):
        note(secret)

    with Scenario("check filtering"):
        check_filtering(secret=secret)

    with Scenario("in another process"):
        with ProcessPool() as pool:
            Scenario(test=check_filtering, parallel=True, executor=pool)(secret=secret)

    with When(f"in test name {secret.value}"):
        pass

    with When("in examples", examples=Examples("x y", [(secret.value, secret.value)])):
        pass

    with When("in value"):
        value("test", {secret.value: secret.value})

    with When("in tag value", tags=[secret.value, secret.value]):
        pass

    with When("in description", description=f"{secret.value}"):
        pass

    with When("in result"):
        xfail(secret.value, reason=f"{secret.value}")

    with When("in metric"):
        metric("test", units="", value=f"{secret.value}")

    with When("creating secrets with duplicate names"):
        Secret("my_duplicate")("hello")
        with raises(ValueError):
            Secret("my_duplicate")("there")

    with When("creating secrets using context manager"):
        with Secret("my_duplicate_2")("hello"):
            with raises(ValueError):
                Secret("my_duplicate_2")("there")
        with Secret("my_duplicate_2")("hello"):
            pass

    with When("RSASecret object"):
        s = RSASecret("my RSA encrypted secret")


if main():
    feature()
