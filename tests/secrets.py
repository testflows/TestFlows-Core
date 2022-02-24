from testflows.core import *

def argparser(parser):
    parser.add_argument("-s", "--secret", type=Secret(name="secret"), metavar="secret", help="secret value", required=True)


@TestModule
@ArgumentParser(argparser)
def feature(self, secret):
    """Test basic usage of secret.
    """
    with When("secret object"):
        note(secret)
    
    with When("in note, debug, trace"):
        note(secret.value)
        debug(secret.value)
        trace(secret.value)
    
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

    with When("RSASecret object"):
        s = RSASecret("my RSA encrypted secret")

if main():
    feature()
