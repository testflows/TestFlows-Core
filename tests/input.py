from testflows.core import *


@TestFeature
@Flags(MANUAL)
@Name("user input")
@Attributes(("name", "value"), ("name2", "value2"))
@Requirements(Requirement("RQ1", version="1.0"))
@Specifications(Specification("SRS001", content=""))
def feature(self):
    """Check reading input from user."""
    with Scenario("test 1", attributes=[Attribute("name", "value")]):
        with When("I ask for input with case insensitive choices"):
            note(input("Enter y/n?", choices=("Y", "N"), lower=True))

        with And("I do something and I grab note from the user", flags=AUTO):
            note(input("Enter a note"))

        with And("I do something and grab debug message form the user", flags=AUTO):
            debug(input("Enter a debug message"))

        with And("I do something and grab trace message form the user", flags=AUTO):
            trace(input("Enter a trace message"))

        metric("my metric", units="sec", value=10.00)
        ticket("JR132442", link="http://localhost:3000")
        value("my value", value="hello there")
        with When("I do something else and grab a message from the user", flags=AUTO):
            message(input("Enter some message", multiline=True))

        # with When("I re-do something and pause", flags=MANUAL):
        #    pause()


if main():
    feature()
