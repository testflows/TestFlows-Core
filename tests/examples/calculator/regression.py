from steps import *


def argparser(parser):
    """Custom test program arguments."""
    parser.add_argument(
        "--local", action="store_true", help="use local web browser", default=False
    )

    parser.add_argument(
        "--webdriver",
        type=str,
        metavar="path",
        dest="local_webdriver_path",
        help=(
            "path to the locally installed driver, default: '/snap/bin/chromium.chromedriver'. "
            "On Ubuntu you should use '/snap/bin/chromium.chromedriver' or just 'chromium.chromedriver'. "
            "For example: './regression --use-local-webdriver --webdriver chromium.chromedriver'."
        ),
        default="/snap/bin/chromium.chromedriver",
    )

    return parser


@TestSketch(Scenario)
def check_basic_operations(self):
    """Check basic operations `+`, `-`, `*`, `/`
    with some one digit positive or negative numbers including `0`.
    """
    try:
        with When("I enter either positive or negative 0,1,2"):
            if either(True, False):
                By(test=press_minus)()
            By(test=either(press_0, press_1, press_2))()

        with And("then I press either +, -, *, / operation"):
            By(test=either(press_plus, press_minus, press_multiply, press_divide))()

        with And("I enter second argument either positive or negative 0,1,2"):
            if either(True, False):
                By(test=press_minus)()
            By(test=either(press_0, press_1, press_2))()

        with And("I press equals to calculate the result"):
            By(test=press_equal)()

        with Then("I check calculator state"):
            By(test=check_state)()
    finally:
        with Finally("I reset calculator back to 0"):
            By(test=reset_calculator)()


@TestModule
@ArgumentParser(argparser)
def regression(self, local=False, local_webdriver_path=None):
    """Calculator regression module."""
    if not local:
        with Given("remote environment"):
            self.env = create_env(
                directory=os.path.join(current_dir(), "docker-compose")
            )

    with Given("webdriver"):
        self.context.webdriver = webdriver(
            local=local, executable_path=local_webdriver_path
        )

    with And("open calculator"):
        open_calculator()

    Scenario(run=check_basic_operations)


if main():
    regression()
