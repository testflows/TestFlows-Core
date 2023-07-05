import os
import hashlib

from testflows.core import *
from testflows.asserts import error, values
from testflows.connect import Shell

from selenium import webdriver as selenium_webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By as SelectBy
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


from contextlib import contextmanager


def sha1_encoder(value):
    return hashlib.sha1(repr(value).encode("utf-8")).hexdigest()


@TestStep(Given)
def webdriver(
    self,
    local=False,
    browser="chrome",
    selenium_hub_url="http://127.0.0.1:4444/wd/hub",
    timeout=60,
    prefs=None,
    no_sandbox=False,
    headless=False,
    executable_path=None,
    implicit_wait_time=60,
    incognito=True,
    disable_infobars=True,
    start_maximized=True,
):
    """Open either local or remote webdriver."""

    if prefs is None:
        prefs = {"download.default_directory": "/tmp/download"}

    arguments = []
    if no_sandbox:
        arguments.append("--no-sandbox")
    if headless:
        arguments.append("--headless")
    if incognito:
        arguments.append("--incognito")
    if disable_infobars:
        arguments.append("disable-infobars")
    if start_maximized:
        arguments.append("start-maximized")

    try:
        if local:
            with By("opening webdriver to local browser"):
                if browser == "chrome":
                    chrome_options = selenium_webdriver.ChromeOptions()
                    for argument in arguments:
                        chrome_options.add_argument(argument)
                    chrome_options.add_experimental_option("prefs", prefs)
                    driver = selenium_webdriver.Chrome(
                        options=chrome_options, executable_path=executable_path
                    )
                else:
                    raise ValueError("only chrome browser is supported")
        else:
            with By("opening webdriver to remote hub"):
                for attempt in retries(timeout=timeout, delay=1, initial_delay=3):
                    with attempt:
                        driver = selenium_webdriver.Remote(
                            command_executor=selenium_hub_url,
                            desired_capabilities={
                                "browserName": browser,
                                "javascriptEnabled": True,
                            },
                        )

        with And(
            "I set implicit wait time",
            description=f"{implicit_wait_time} sec",
        ):
            driver.implicit_wait = implicit_wait_time
            driver.implicitly_wait(implicit_wait_time)

        yield driver

    finally:
        with Finally("close webdriver"):
            driver.close()


@contextmanager
def SystemTerminal(default_timeout=100, name=None):
    """Create system terminal."""
    with Shell(name=name) as terminal:
        terminal.timeout = default_timeout
        yield terminal


class DockerComposeEnv:
    def __init__(
        self,
        project_directory=None,
        yml_file="docker-compose.yml",
        executable="docker-compose",
    ):
        self.docker_compose = f"{executable}"
        self.docker_compose += f' --ansi never --project-directory "{project_directory}" --file "{os.path.join(project_directory, yml_file)}"'

    def up(self, timeout=600, renew_anon_volumes=True, force_recreate=True):
        """Bring docker-compose environment up."""
        command = f"{self.docker_compose} up"

        if renew_anon_volumes:
            command += " --renew-anon-volumes"

        if force_recreate:
            command += " --force-recreate"

        if timeout:
            command += f" --timeout {timeout}"

        with SystemTerminal() as terminal:
            cmd = terminal(f"set -o pipefail && {command} -d 2>&1 | tee", timeout=600)
            assert cmd.exitcode == 0, error()

    def down(self, timeout=60, verbose=True, remove_orphans=True):
        """Bring docker-compose environment down."""
        command = f"{self.docker_compose} down"

        if verbose:
            command += " -v"

        if remove_orphans:
            command += " --remove-orphans"

        if timeout:
            command += f" --timeout {timeout}"

        with SystemTerminal() as terminal:
            cmd = terminal(f"set -o pipefail && {command} 2>&1 | tee")
            assert cmd.exitcode == 0, error()


@TestStep(Given)
def create_env(self, directory):
    """Create docker-compose UI testing environment."""

    with By("creating docker-compose environment"):
        docker_compose_env = DockerComposeEnv(project_directory=directory)

    try:
        with And("bringing docker-compose up"):
            docker_compose_env.up()

        yield docker_compose_env

    finally:
        with Finally("I bring docker-compose down"):
            docker_compose_env.down()


@TestStep
def open_google(self):
    """Open Google."""
    driver: WebDriver = self.context.webdriver

    with By("opening Google URL"):
        driver.get("https://www.google.com/?q=")

    with Then("checking title is present"):
        assert driver.title == "Google", error()


@TestStep
def search_for_calculator(self, delay=0.2):
    """Search for calculator."""
    driver: WebDriver = self.context.webdriver

    with By("finding search box"):
        search_box = wait_for_elements_to_be_visible(
            select_type=SelectBy.CSS_SELECTOR, element="textarea[name='q']"
        )[0]

    with And("entering calculator"):
        search_box.send_keys("calculator")

    with And("submitting the search"):
        search_box.submit()

    with And("checking title calculator title is present"):
        assert driver.title == "calculator - Google Search", error()

    with And("waiting for calculator to appear"):
        wait_for_elements_to_be_visible(
            select_type=SelectBy.CSS_SELECTOR, element="#rso > div:nth-of-type(1)"
        )


@TestStep
def type_text(self, text):
    """Type text."""
    driver: WebDriver = self.context.webdriver

    div = driver.find_element(
        SelectBy.XPATH, f'//*[@id="rso"]//div[@role="presentation"]'
    )
    div.send_keys(text)


@TestStep
def find_button(self, text=None, arial_label=None):
    """Find and return button element."""
    driver: WebDriver = self.context.webdriver

    if arial_label is not None:
        button = driver.find_element(
            SelectBy.XPATH,
            f'//*[@id="rso"]//div[@role="button" and @aria-label="{arial_label}"]',
        )
    elif text is not None:
        button = driver.find_element(
            SelectBy.XPATH, f'//*[@id="rso"]//div[@role="button"][text()="{text}"]'
        )
    else:
        raise ValueError("either button text value or arial label must be specified")

    return button


@TestStep
def press_button(self, text=None, arial_label=None):
    """Press button."""
    note(f"press {text if text is not None else arial_label}")
    button = find_button(text=text, arial_label=arial_label)
    button.click()


@TestStep
def is_button_displayed(self, text=None, arial_label=None):
    """Return True of button is visible."""
    button = find_button(text=text, arial_label=arial_label)
    return button.is_displayed()


@TestStep(Then)
def get_display(self):
    """Get display."""
    driver: WebDriver = self.context.webdriver

    result_box = wait_for_elements_to_be_visible(
        select_type=SelectBy.XPATH,
        element='//*[@id="rso"]//div[@role="presentation"]/div/span',
    )[0]
    return result_box.get_attribute("textContent")


@TestStep(Then)
def get_answer_prompt(self):
    """Get answer prompt."""
    driver: WebDriver = self.context.webdriver

    answer_prompt = wait_for_elements_to_be_visible(
        select_type=SelectBy.XPATH,
        element="//*[@id='rso']//h2[text()='Calculator Result']/following-sibling::div/div/div/following-sibling::div/div/div/span",
    )[0]
    return answer_prompt.get_attribute("textContent")


def wait_for_elements_to_be_visible(select_type=None, element=None, timeout=30):
    """Wait for elements to be present."""
    driver: WebDriver = current().context.webdriver

    wait = WebDriverWait(driver, timeout)
    wait.until(EC.visibility_of_element_located((select_type, element)))

    return driver.find_elements(select_type, element)


def wait_for_element_to_be_visible(select_type=None, element=None, timeout=30):
    """Wait for elements to be present."""
    elements = wait_for_elements_to_be_visible(
        select_type=select_type, element=element, timeout=timeout
    )
    return elements[0]


def wait_for_elements_to_be_clickable(
    timeout=None, poll_frequency=None, select_type=None, element=None
):
    """Wait for elements to be clickable."""
    driver: WebDriver = current().context.webdriver

    if timeout is None:
        timeout = 30
    if poll_frequency is None:
        poll_frequency = 1

    wait = WebDriverWait(driver, timeout=timeout, poll_frequency=poll_frequency)
    wait.until(EC.element_to_be_clickable((select_type, element)))

    return driver.find_elements(select_type, element)


def wait_for_element_to_be_clickable(
    timeout=None, poll_frequency=None, select_type=None, element=None
):
    elements = wait_for_elements_to_be_clickable(
        timeout=timeout,
        poll_frequency=poll_frequency,
        select_type=select_type,
        element=element,
    )
    return elements[0]


@TestStep(Given)
def open_calculator(self):
    """Open calculator."""
    open_google()
    search_for_calculator()


@TestStep(When)
def press_0(self):
    """Press '0' button."""
    press_button(text="0")


@TestStep(When)
def type_0(self):
    """Input '0'."""
    type_text(text="0")


@TestStep(When)
def press_1(self):
    """Press '1' button."""
    press_button(text="1")


@TestStep(When)
def type_1(self):
    """Input '1'."""
    type_text(text="1")


@TestStep(When)
def press_2(self):
    """Press '2' button."""
    press_button(text="2")


@TestStep(When)
def type_2(self):
    """Input '2'."""
    type_text(text="2")


@TestStep(When)
def press_3(self):
    """Press '3' button."""
    press_button(text="3")


@TestStep(When)
def type_3(self):
    """Input '3'."""
    type_text(text="3")


@TestStep(When)
def press_4(self):
    """Press '4' button."""
    press_button(text="4")


@TestStep(When)
def type_4(self):
    """Input '4'."""
    type_text(text="4")


@TestStep(When)
def press_5(self):
    """Press '5' button."""
    press_button(text="5")


@TestStep(When)
def type_5(self):
    """Input '5'."""
    type_text(text="5")


@TestStep(When)
def press_6(self):
    """Press '6' button."""
    press_button(text="6")


@TestStep(When)
def type_6(self):
    """Input '6'."""
    type_text(text="6")


@TestStep(When)
def press_7(self):
    """Press '7' button."""
    press_button(text="7")


@TestStep(When)
def type_7(self):
    """Input '7'."""
    type_text(text="7")


@TestStep(When)
def press_8(self):
    """Press '8' button."""
    press_button(text="8")


@TestStep(When)
def type_8(self):
    """Input '8'."""
    type_text(text="8")


@TestStep(When)
def press_9(self):
    """Press '9' button."""
    press_button(text="9")


@TestStep(When)
def type_9(self):
    """Input '9'."""
    type_text(text="9")


@TestStep(When)
def press_plus(self):
    """Press '+' button."""
    press_button(arial_label="plus")


@TestStep(When)
def type_plus(self):
    """Input '+'."""
    type_text(text="+")


@TestStep(When)
def press_minus(self):
    """Press '-' button."""
    press_button(arial_label="minus")


@TestStep(When)
def type_minus(self):
    """Input '-'."""
    type_text(text="-")


@TestStep(When)
def press_multiply(self):
    """Press '×' button."""
    press_button(arial_label="multiply")


@TestStep(When)
def type_multiply(self):
    """Input '*'."""
    type_text(text="*")


@TestStep(When)
def press_divide(self):
    """Press '÷' button."""
    press_button(arial_label="divide")


@TestStep(When)
def type_divide(self):
    """Input '/'."""
    type_text(text="/")


@TestStep(When)
def press_clear(self):
    """Press 'CE/AC' button."""
    if is_button_displayed(arial_label="clear entry"):
        press_button(arial_label="clear entry")
    else:
        press_button(arial_label="all clear")


@TestStep(When)
def check_clear(self, mode=None):
    """Check if clear button is in CE or AC mode."""
    with By("getting clear mode"):
        current_mode = "AC"

        if is_button_displayed(arial_label="clear entry"):
            current_mode = "CE"

    if mode is not None:
        assert current_mode == mode, error()

    return current_mode


@TestStep(When)
def type_clear(self):
    """Input 'Backspace' button."""
    type_text(text=Keys.BACKSPACE)


@TestStep(When)
def press_percentage(self):
    """Press '%' button."""
    press_button(arial_label="percentage")


@TestStep(When)
def type_percentage(self):
    """Input '%'."""
    type_text(text="%")


@TestStep(When)
def press_left_parenthesis(self):
    """Press '(' button."""
    press_button(arial_label="left parenthesis")


@TestStep(When)
def type_left_parenthesis(self):
    """Input '()'."""
    type_text(text="(")


@TestStep(When)
def press_right_parenthesis(self):
    """Press ')' button."""
    press_button(arial_label="right parenthesis")


@TestStep(When)
def type_right_parenthesis(self):
    """Input ')'."""
    type_text(text=")")


@TestStep(When)
def press_dot(self):
    """Press '.' button."""
    press_button(arial_label="point")


@TestStep(When)
def type_dot(self):
    """Input '.'."""
    type_text(text=".")


@TestStep(When)
def press_equal(self):
    """Press '=' button."""
    press_button(arial_label="equals")


@TestStep(When)
def type_equal(self):
    """Input '='."""
    type_text(text="=")


@TestStep(When)
def type_enter(self):
    """Input 'ENTER'."""
    type_text(text=Keys.ENTER)


@TestStep(When)
def press_factorial(self):
    """Press 'x!' button."""
    press_button(arial_label="factorial")


@TestStep(When)
def type_factorial(self):
    """Input '!'."""
    type_text(text="!")


@TestStep(When)
def press_sine(self):
    """Press 'sin' button."""
    press_button(arial_label="sine")


@TestStep(When)
def type_sine(self):
    """Input 's'."""
    type_text(text="s")


@TestStep(When)
def press_cosine(self):
    """Press 'cos' button."""
    press_button(arial_label="cosine")


@TestStep(When)
def type_cosine(self):
    """Input 'c'."""
    type_text(text="c")


@TestStep(When)
def press_natural_logarithm(self):
    """Press 'ln' button."""
    press_button(arial_label="natural logarithm")


@TestStep(When)
def type_natural_logarithm(self):
    """Input 'l'."""
    type_text(text="l")


@TestStep(When)
def type_natural_logarithm2(self):
    """Input 'L'."""
    type_text(text="L")


@TestStep(When)
def press_logarithm(self):
    """Press 'log' button."""
    press_button(arial_label="logarithm")


@TestStep(When)
def type_logarithm(self):
    """Input 'g'."""
    type_text(text="g")


@TestStep(When)
def type_logarithm2(self):
    """Input 'G'."""
    type_text(text="G")


@TestStep(When)
def press_pi(self):
    """Press 'π' button."""
    press_button(arial_label="pi")


@TestStep(When)
def type_pi(self):
    """Input 'p'."""
    type_text(text="p")


@TestStep(When)
def type_pi2(self):
    """Input 'P'."""
    type_text(text="P")


@TestStep(When)
def press_eulers_number(self):
    """Press 'e' button."""
    press_button(arial_label="euler's number")


@TestStep(When)
def type_eulers_number(self):
    """Input 'e'."""
    type_text(text="e")


@TestStep(When)
def press_tangent(self):
    """Press 'tan' button."""
    press_button(arial_label="tangent")


@TestStep(When)
def type_tangent(self):
    """Input 't'."""
    type_text(text="t")


@TestStep(When)
def press_square_root(self):
    """Press '√' button."""
    press_button(arial_label="square root")


@TestStep(When)
def type_square_root(self):
    """Input 'q'."""
    type_text(text="q")


@TestStep(When)
def type_square_root2(self):
    """Input 'Q'."""
    type_text(text="Q")


@TestStep(When)
def press_answer(self):
    """Press 'Ans' button."""
    press_button(arial_label="answer")


@TestStep(When)
def type_answer(self):
    """Input 'a'."""
    type_text(text="a")


@TestStep(When)
def type_answer2(self):
    """Input 'a'."""
    type_text(text="A")


@TestStep(When)
def press_exponential(self):
    """Press 'exp' button."""
    press_button(arial_label="exponential")


@TestStep(When)
def type_exponential(self):
    """Input 'E'."""
    type_text(text="E")


@TestStep(When)
def press_x_power_y(self):
    """Press 'x^y' button."""
    press_button(arial_label="X to the power of Y")


@TestStep(When)
def type_x_power_y(self):
    """Input '^'."""
    type_text(text="^")


def set_rad_deg_mode(state):
    """Set Inv mode."""
    current_mode = getattr(state, "rad_deg", "Deg")
    state.rad_deg = "Rad" if current_mode == "Deg" else "Deg"


@TestStep(When)
def press_rad_deg(self):
    """Press 'Rad|Deg' button."""
    press_button(arial_label="switch between radians and degrees")


def set_inverse_mode(state):
    """Set inverse mode."""
    state.inv = not getattr(state, "inverse", False)


def inverse_mode(state):
    """Return True if inverse mode is set."""
    return getattr(state, "inverse", False)


@TestStep(When)
def press_inverse(self):
    """Press 'Inv' button."""
    press_button(arial_label="inverse")


@TestStep(When)
def press_arcsine(self):
    """Press 'arcsine' button."""
    press_button(arial_label="arcsine")


@TestStep(When)
def type_arcsine(self):
    """Input 'S'."""
    type_text(text="S")


@TestStep(When)
def press_arccosine(self):
    """Press 'arccos' button."""
    press_button(arial_label="arccosine")


@TestStep(When)
def type_arccosine(self):
    """Input 'C'."""
    type_text(text="C")


@TestStep(When)
def press_arctangent(self):
    """Press 'arctan' button."""
    press_button(arial_label="arctangent")


@TestStep(When)
def type_arctangent(self):
    """Input 'T'."""
    type_text(text="T")


@TestStep(When)
def press_random(self):
    """Press 'Rnd' button."""
    press_button(arial_label="random")


@TestStep(When)
def type_random(self):
    """Input 'R'."""
    type_text(text="R")


@TestStep(When)
def press_e_to_the_power_of_x(self):
    """Press 'e^x' button."""
    press_button(arial_label="E to the power of X")


@TestStep(When)
def press_ten_to_the_power_of_x(self):
    """Press '10^x' button."""
    press_button(arial_label="ten to the power of X")


@TestStep(When)
def press_square(self):
    """Press 'x^2' button."""
    press_button(arial_label="square")


@TestStep(When)
def press_y_root_of_x(self):
    """Press 'Y root of x' button."""
    press_button(arial_label="Y root of X")


@TestStep(When)
def type_y_root_of_x(self):
    """Input 'r'."""
    type_text(text="r")


@TestStep(Then)
def check_answer_prompt(self, prompt=None):
    """Check current answer prompt."""
    current_prompt = get_answer_prompt()
    if prompt is not None:
        assert current_prompt == prompt, error()

    return current_prompt


@TestStep(Then)
def check_display(
    self, value=None, count=1, timeout=None, delay=0.2, initial_delay=0.01
):
    """Check result."""
    for attempt in retries(
        count=count, timeout=timeout, delay=delay, initial_delay=initial_delay
    ):
        with attempt:
            with By("getting display"):
                result = get_display()
            if value is not None:
                with Then("checking if it matches value"):
                    assert result == value, f"'{result}' != '{value}'"
            else:
                break
    return result


@TestStep(Then)
def check_state(self, display=None, clear=None, answer_prompt=None, timeout=0.1):
    display = check_display(value=display)
    clear = check_clear(mode=clear)
    answer_prompt = check_answer_prompt(prompt=answer_prompt)

    debug(f"{display} {clear} {answer_prompt}")


@TestStep(When)
def reset_calculator(self):
    """Reset calculator."""
    press_0()
    press_equal()
    press_clear()
