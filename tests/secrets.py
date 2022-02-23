from testflows.core import *

def argparser(parser):
    parser.add_argument("-s", "--secret", type=Secret(name="secret"), metavar="secret", help="secret value", required=True)


@TestModule
@ArgumentParser(argparser)
def feature(self, secret):
    """Test basic usage of secret.
    """
    with When("I use secret object"):
        note(secret)
    
    with When("I use secret value"):
        note(secret.value)
        note("bobo")
    
    with When("bobo"):
        pass

if main():
    feature()
