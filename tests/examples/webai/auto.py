# Copyright 2024 Katteli Inc.
# TestFlows.com Open-Source Software Testing Framework (http://testflows.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# 
# Major parts ported from the Auto-Playwright project (https://github.com/lucgagan/auto-playwright/blob/main/LICENSE)
# Copyright (c) 2023 Luc Gagan (https://ray.run/)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import uuid
import json

from contextlib import contextmanager
from bs4 import BeautifulSoup

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By

from testflows.core import current, debug, When, And, Then, Step
from testflows.core.name import basename

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool


def get_page_source(webdriver: WebDriver):
    """Return current page source."""
    return webdriver.page_source


def sanitize_html(html: str, allowed_tags: list = None) -> str:
    """
    Sanitize HTML by removing all tags except those in the allowed_tags list.

    Args:
        html (str): The HTML content to sanitize.
        allowed_tags (list): List of allowed HTML tags (e.g., ['p', 'b', 'i']).

    Returns:
        str: Sanitized HTML.
    """
    if allowed_tags is None:
        allowed_tags = [
            "address",
            "article",
            "aside",
            "footer",
            "header",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "hgroup",
            "main",
            "nav",
            "section",
            "blockquote",
            "dd",
            "div",
            "dl",
            "dt",
            "figcaption",
            "figure",
            "hr",
            "li",
            "main",
            "ol",
            "p",
            "pre",
            "ul",
            "a",
            "abbr",
            "b",
            "bdi",
            "bdo",
            "br",
            "cite",
            "code",
            "data",
            "dfn",
            "em",
            "i",
            "kbd",
            "mark",
            "q",
            "rb",
            "rp",
            "rt",
            "rtc",
            "ruby",
            "s",
            "samp",
            "small",
            "span",
            "strong",
            "sub",
            "sup",
            "time",
            "u",
            "var",
            "wbr",
            "caption",
            "col",
            "colgroup",
            "table",
            "tbody",
            "td",
            "tfoot",
            "th",
            "thead",
            "tr",
        ]
        allowed_tags += [
            "button",
            "form",
            "img",
            "input",
            "select",
            "textarea",
        ]
    # Parse the HTML
    soup = BeautifulSoup(html, "html.parser")

    # Iterate over all tags in the HTML
    for tag in soup.find_all(True):  # True matches all tags
        if tag.name not in allowed_tags:
            tag.unwrap()  # Remove the tag but keep its content

    return str(soup)


# Define custom tools
def get_locator(element_id: str):
    """
    Retrieve a WebElement from the locator map using its unique element ID.

    Args:
        element_id (str): The unique identifier for the element.

    Returns:
        WebElement: The located WebElement.

    Raises:
        ValueError: If the element ID is not found in the locator map.
    """
    # Retrieve the WebElement from the locator map
    locator = current().context.locator_map.get(element_id)

    if not locator:
        raise ValueError(f'Unknown elementId "{element_id}"')

    return locator


@tool
def locate_element(cssSelector: str) -> str:
    """
    Locate an element on the page using a CSS selector.

    Args:
        cssSelector (str): The CSS selector to locate the element.

    Returns:
        str: an `elementId` that can be used for future operations.
    """
    test = current()
    try:
        # Locate the element using the CSS selector
        element = test.context.webdriver.find_element(By.CSS_SELECTOR, cssSelector)

        # Generate a unique ID for the element
        element_id = str(uuid.uuid4())

        debug(
            f"Located element with selector '{cssSelector}' and assigned ID '{element_id}'"
        )

        # Store the element in the locator map
        test.context.locator_map[element_id] = element

        # Return the element ID
        return element_id
    except Exception as e:
        raise ValueError(f"Failed to locate element with selector '{cssSelector}': {e}")


@tool
def locator_evaluate(elementId: str, pageFunction: str) -> str:
    """
    Evaluate JavaScript code in the page context, using a WebElement.

    Args:
        elementId (str): The unique ID of the element.
        pageFunction (str): JavaScript function to evaluate on the element.

    Returns:
        str: Result of the evaluation.
    """
    try:
        # Retrieve the WebElement using its element ID
        element = get_locator(elementId)

        # Execute JavaScript in the page context
        result = current().context.webdriver.execute_script(
            f"return ({pageFunction})(arguments[0]);", element
        )

        return str(result)
    except ValueError as e:
        raise ValueError(f"Failed to evaluate script: {e}")
    except Exception as e:
        raise ValueError(f"An error occurred while evaluating the script: {e}")


@tool
def locator_getAttribute(elementId: str, attributeName: str) -> str:
    """
    Get the value of an attribute for a specified element.

    Args:
        elementId (str): The unique ID of the element.
        attributeName (str): The name of the attribute to retrieve.

    Returns:
        str: containing the attribute value.
    """
    try:
        # Retrieve the WebElement using its element ID
        element = get_locator(elementId)

        # Get the attribute value
        attribute_value = element.get_attribute(attributeName)

        return str(attribute_value)
    except ValueError as e:
        raise ValueError(f"Failed to get attribute: {e}")
    except Exception as e:
        raise ValueError(f"An error occurred while getting the attribute: {e}")


@tool
def locator_innerHTML(elementId: str) -> str:
    """
    Get the innerHTML of a specified element.

    Args:
        elementId (str): The unique ID of the element.

    Returns:
        str: innerHTML of the element.
    """
    try:
        # Retrieve the WebElement using its element ID
        element = get_locator(elementId)

        # Get the innerHTML using the get_attribute method
        inner_html = element.get_attribute("innerHTML")

        return str(inner_html)
    except ValueError as e:
        raise ValueError(f"Failed to get innerHTML: {e}")
    except Exception as e:
        raise ValueError(f"An error occurred while getting innerHTML: {e}")


@tool
def locator_innerText(elementId: str) -> str:
    """
    Get the innerText of a specified element.

    Args:
        elementId (str): The unique ID of the element.

    Returns:
        str: the innerText of the element.
    """
    try:
        # Retrieve the WebElement using its element ID
        element = get_locator(elementId)

        # Get the innerText using the 'text' property
        inner_text = element.text

        return str(inner_text)
    except ValueError as e:
        raise ValueError(f"Failed to get innerText: {e}")
    except Exception as e:
        raise ValueError(f"An error occurred while getting innerText: {e}")


@tool
def locator_textContent(elementId: str) -> str:
    """
    Get the textContent of a specified element.

    Args:
        elementId (str): The unique ID of the element.

    Returns:
        str: The textContent of the element.
    """
    try:
        # Retrieve the WebElement using its element ID
        element = get_locator(elementId)

        # Get the textContent using the 'textContent' attribute
        text_content = element.get_attribute("textContent")

        return text_content
    except ValueError as e:
        raise ValueError(f"Failed to get textContent: {e}")
    except Exception as e:
        raise ValueError(f"An error occurred while getting textContent: {e}")


@tool
def locator_inputValue(elementId: str) -> str:
    """
    Get the input value of a specified <input>, <textarea>, or <select> element.

    Args:
        elementId (str): The unique ID of the element.

    Returns:
        str: The value of the input element.
    """
    try:
        # Retrieve the WebElement using its element ID
        element = get_locator(elementId)

        # Get the input value using the 'value' attribute
        input_value = element.get_attribute("value")

        return input_value
    except ValueError as e:
        raise ValueError(f"Failed to get input value: {e}")
    except Exception as e:
        raise ValueError(f"An error occurred while getting input value: {e}")


@tool
def locator_blur(elementId: str) -> bool:
    """
    Removes keyboard focus from the specified element.

    Args:
        elementId (str): The unique ID of the element.

    Returns:
        bool: True if the operation was successful.
    """
    try:
        # Retrieve the WebElement using its element ID
        element = get_locator(elementId)

        # Remove focus from the element by executing JavaScript
        # `blur()` is not directly supported by Selenium, so we use JavaScript
        element.parent.execute_script("arguments[0].blur();", element)

        return True
    except ValueError as e:
        raise ValueError(f"Failed to blur element: {e}")
    except Exception as e:
        raise ValueError(f"An error occurred while removing focus: {e}")


@tool
def locator_boundingBox(elementId: str) -> str:
    """
    Get the bounding box of a specified element.

    Args:
        elementId (str): The unique ID of the element.

    Returns:
        str: A dictionary containing x, y, width, and height of the element's bounding box.
    """
    try:
        # Retrieve the WebElement using its element ID
        element = get_locator(elementId)

        # Get the bounding rectangle using Selenium's location and size properties
        location = element.location
        size = element.size

        # Create the bounding box object
        bounding_box = json.dumps(
            {
                "x": location["x"],
                "y": location["y"],
                "width": size["width"],
                "height": size["height"],
            }
        )

        return bounding_box
    except ValueError as e:
        raise ValueError(f"Failed to get bounding box: {e}")
    except Exception as e:
        raise ValueError(f"An error occurred while getting bounding box: {e}")


@tool
def locator_check(elementId: str) -> bool:
    """
    Ensure that a checkbox or radio element is checked.

    Args:
        elementId (str): The unique ID of the element.

    Returns:
        bool: True if the operation is successful.
    """
    try:
        # Retrieve the WebElement using its element ID
        element = get_locator(elementId)

        # Check if the element is already selected
        if not element.is_selected():
            # Click the element to check it
            element.click()

        return True
    except ValueError as e:
        raise ValueError(f"Failed to check element: {e}")
    except Exception as e:
        raise ValueError(f"An error occurred while checking the element: {e}")


@tool
def locator_uncheck(elementId: str) -> bool:
    """
    Ensure that a checkbox is unchecked.

    Args:
        elementId (str): The unique ID of the checkbox element.

    Returns:
        bool: True if the operation is successful.
    """
    try:
        # Retrieve the WebElement using its element ID
        element = get_locator(elementId)

        # Check if the element is currently selected
        if element.is_selected():
            # Click the element to uncheck it
            element.click()

        return True
    except ValueError as e:
        raise ValueError(f"Failed to uncheck element: {e}")
    except Exception as e:
        raise ValueError(f"An error occurred while unchecking the element: {e}")


@tool
def locator_isChecked(elementId: str) -> bool:
    """
    Check whether a checkbox or radio element is checked.

    Args:
        elementId (str): The unique ID of the element.

    Returns:
        bool: True if the element is checked, otherwise False.
    """
    try:
        # Retrieve the WebElement using its element ID
        element = get_locator(elementId)

        # Check if the element is selected
        return element.is_selected()
    except ValueError as e:
        raise ValueError(f"Failed to check element state: {e}")
    except Exception as e:
        raise ValueError(f"An error occurred while checking the element state: {e}")


@tool
def locator_isEditable(elementId: str) -> bool:
    """
    Check whether an element is editable.

    Args:
        elementId (str): The unique ID of the element.

    Returns:
        bool: True if the element is editable, otherwise False.
    """
    try:
        # Retrieve the WebElement using its element ID
        element = get_locator(elementId)

        # Check if the element is enabled and does not have the 'readonly' attribute
        is_enabled = element.is_enabled()
        is_readonly = element.get_attribute("readonly") is not None

        return is_enabled and not is_readonly
    except ValueError as e:
        raise ValueError(f"Failed to check if element is editable: {e}")
    except Exception as e:
        raise ValueError(
            f"An error occurred while checking if the element is editable: {e}"
        )


@tool
def locator_isEnabled(elementId: str) -> bool:
    """
    Check whether an element is enabled.

    Args:
        elementId (str): The unique ID of the element.

    Returns:
        bool: True if the element is enabled, otherwise False.
    """
    try:
        # Retrieve the WebElement using its element ID
        element = get_locator(elementId)

        # Check if the element is enabled
        return element.is_enabled()
    except ValueError as e:
        raise ValueError(f"Failed to check if element is enabled: {e}")
    except Exception as e:
        raise ValueError(
            f"An error occurred while checking if the element is enabled: {e}"
        )


@tool
def locator_isVisible(elementId: str) -> bool:
    """
    Check whether an element is visible.

    Args:
        elementId (str): The unique ID of the element.

    Returns:
        bool: True if the element is visible, otherwise False.
    """
    try:
        # Retrieve the WebElement using its element ID
        element = get_locator(elementId)

        # Check if the element is displayed
        return element.is_displayed()
    except ValueError as e:
        raise ValueError(f"Failed to check if element is visible: {e}")
    except Exception as e:
        raise ValueError(
            f"An error occurred while checking if the element is visible: {e}"
        )


@tool
def locator_clear(elementId: str) -> bool:
    """
    Clear the content of an input field.

    Args:
        elementId (str): The unique ID of the input field element.

    Returns:
        bool: True if the operation is successful.
    """
    try:
        # Retrieve the WebElement using its element ID
        element = get_locator(elementId)

        # Clear the input field
        element.clear()

        return True
    except ValueError as e:
        raise ValueError(f"Failed to clear the input field: {e}")
    except Exception as e:
        raise ValueError(f"An error occurred while clearing the input field: {e}")


@tool
def locator_click(elementId: str) -> bool:
    """
    Click an element.

    Args:
        elementId (str): The unique ID of the element.

    Returns:
        bool: True if the operation is successful.
    """
    try:
        # Retrieve the WebElement using its element ID
        element = get_locator(elementId)

        # Perform a click on the element
        element.click()

        return True
    except ValueError as e:
        raise ValueError(f"Failed to click the element: {e}")
    except Exception as e:
        raise ValueError(f"An error occurred while clicking the element: {e}")


@tool
def locator_count(cssSelector: str) -> int:
    """
    Count the number of elements matching a CSS selector.

    Args:
        cssSelector (str): The CSS selector to locate elements.

    Returns:
        int: The number of elements matching the selector.
    """
    try:
        # Locate all elements matching the CSS selector
        elements = current().context.webdriver.find_elements(
            By.CSS_SELECTOR, cssSelector
        )

        # Return the count of elements
        return len(elements)
    except Exception as e:
        raise ValueError(f"An error occurred while counting elements: {e}")


@tool
def locator_fill(elementId: str, value: str) -> bool:
    """
    Set a value to the input field.

    Args:
        elementId (str): The unique ID of the input field element.
        value (str): The value to set in the input field.

    Returns:
        bool: True if the operation is successful.
    """
    try:
        # Retrieve the WebElement using its element ID
        element = get_locator(elementId)

        # Clear the input field before setting a new value
        element.clear()

        # Set the value in the input field
        element.send_keys(value)

        return True
    except ValueError as e:
        raise ValueError(f"Failed to set value in the input field: {e}")
    except Exception as e:
        raise ValueError(
            f"An error occurred while setting value in the input field: {e}"
        )


@tool
def page_goto(url: str) -> str:
    """
    Navigate the browser to a specified URL.

    Args:
        url (str): The URL to navigate to.

    Returns:
        str: The URL of the page the browser navigated to.
    """
    driver = current().context.webdriver

    try:
        # Navigate to the specified URL
        driver.get(url)

        # Return the current URL after navigation
        return driver.current_url
    except Exception as e:
        raise ValueError(f"Failed to navigate to the URL: {e}")


@tool
def expect_toBe(actual: str, expected: str) -> str:
    """
    Asserts that the actual value is equal to the expected value.

    Args:
        actual (str): The actual value.
        expected (str): The expected value.

    Returns:
        str: A dictionary containing actual, expected, and success (True/False).
    """
    try:
        # Check if the actual value matches the expected value
        success = actual == expected

        # Return the assertion results
        return json.dumps({"actual": actual, "expected": expected, "success": success})
    except Exception as e:
        raise ValueError(f"An error occurred during the assertion: {e}")


@tool
def expect_notToBe(actual: str, expected: str) -> str:
    """
    Asserts that the actual value is not equal to the expected value.

    Args:
        actual (str): The actual value.
        expected (str): The expected value.

    Returns:
        str: A dictionary containing actual, expected, and success (True/False).
    """
    try:
        # Check if the actual value does not match the expected value
        success = actual != expected

        # Return the assertion results
        return json.dumps({"actual": actual, "expected": expected, "success": success})
    except Exception as e:
        raise ValueError(f"An error occurred during the assertion: {e}")


@tool
def result_Assertion(assertion: bool) -> str:
    """
    Handles the result of an assertion.

    Args:
        assertion (bool): The result of the assertion (True for success, False for failure).

    Returns:
        str: containing the assertion result.
    """
    try:
        # Return the assertion result
        return str(assertion)
    except Exception as e:
        raise ValueError(f"An error occurred while handling the assertion result: {e}")


@tool
def result_Query(query: str) -> str:
    """
    Handles the result of a data extraction query.

    Args:
        query (str): The extracted data as a text value.

    Returns:
        str: the query result.
    """
    try:
        # Return the query result
        return query
    except Exception as e:
        raise ValueError(f"An error occurred while handling the query result: {e}")


@tool
def result_Action() -> bool:
    """
    Handles the result of an action.

    This function is called at the end when the initial instructions asked to perform an action.

    Returns:
        bool: always True to indicate the action was successful.
    """
    try:
        # Return None to indicate no result data is required
        return True
    except Exception as e:
        raise ValueError(f"An error occurred while handling the action result: {e}")


@tool
def result_Error(errorMessage: str) -> str:
    """
    Handles error responses when instructions cannot be completed.

    Args:
        errorMessage (str): The error message describing the issue.

    Returns:
        dict: A dictionary containing the error message.
    """
    try:
        # Return the error message as a dictionary
        return json.dumps({"errorMessage": errorMessage})
    except Exception as e:
        raise ValueError(f"An error occurred while handling the error response: {e}")


tools = {
    "locate_element": locate_element,
    "locator_evaluate": locator_evaluate,
    "locator_getattribute": locator_getAttribute,
    "locator_innerhtml": locator_innerHTML,
    "locator_innertext": locator_innerText,
    "locator_textcontent": locator_textContent,
    "locator_inputvalue": locator_inputValue,
    "locator_blur": locator_blur,
    "locator_boundingbox": locator_boundingBox,
    "locator_check": locator_check,
    "locator_uncheck": locator_uncheck,
    "locator_ischecked": locator_isChecked,
    "locator_iseditable": locator_isEditable,
    "locator_isenabled": locator_isEnabled,
    "locator_isvisible": locator_isVisible,
    "locator_clear": locator_clear,
    "locator_click": locator_click,
    "locator_count": locator_count,
    "locator_fill": locator_fill,
    "page_goto": page_goto,
    "expect_tobe": expect_toBe,
    "expect_nottobe": expect_notToBe,
    "result_assertion": result_Assertion,
    "result_query": result_Query,
    "result_action": result_Action,
    "result_error": result_Error,
}

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
llm_with_tools = llm.bind_tools(list(tools.values()))


def prompt(task, snapshot):
    return f"""This is your task: {task}

* When creating CSS selectors, ensure they are unique and specific enough to select only one element, even if there are multiple elements of the same type (like multiple h1 elements).
* Avoid using generic tags like 'h1' alone. Instead, combine them with other attributes or structural relationships to form a unique selector.
* You must not derive data from the page if you are able to do so by using one of the provided functions, e.g. locator_evaluate.
* Some CSS classes may contain an empty space. Handle them accordingly. For example, ".
* There are custom tags such as 'clr-control-helper'. Don't mistake them for CSS classes.

Webpage snapshot:

```
{snapshot}
```
"""


def run(test, task, snapshot):
    """Execute AI task."""
    test.context.locator_map = {}

    messages = [HumanMessage(prompt(task, snapshot))]

    ai_msg = llm_with_tools.invoke(messages)

    while ai_msg.tool_calls:
        messages.append(ai_msg)
        for tool_call in ai_msg.tool_calls:
            selected_tool = tools[tool_call["name"].lower()]
            args = tool_call["args"]
            debug(f"Tool call: {tool_call}")
            try:
                tool_output = selected_tool.invoke(args)
            except Exception as e:
                tool_output = str(e)
            debug(f"Tool output: {tool_output}")
            messages.append(ToolMessage(tool_output, tool_call_id=tool_call["id"]))

        ai_msg = llm_with_tools.invoke(messages)

    messages.append(ai_msg)
    debug(f"{ai_msg}")
    # debug(f"Messages to complete the task: {messages}")
    # for msg in messages:
    #    debug(f"Message: {type(msg)}")


@contextmanager
def Auto(name, description=None, **kwargs):
    """Execute automated AI task."""

    steps = {
        "When": When,
        "And": And,
        "Then": Then,
    }

    if name.startswith("When"):
        step = steps["When"]
        name = name.replace("When", "")
    elif name.startswith("And"):
        step = steps["And"]
        name = name.replace("And", "")
    elif name.startswith("Then"):
        step = steps["Then"]
        name = name.replace("Then", "")
    else:
        step = Step

    name = name.strip()
    # strip "I " from the beginning of the task name
    if name.startswith("I "):
        name = name[2:]

    with step(name, description=description, **kwargs) as test:
        task = name
        if description:
            task += "\n" + description

        debug(f"Task: {task}")

        webdriver = test.context.webdriver

        snapshot = sanitize_html(get_page_source(webdriver))[:3000]
        # debug(f"Snapshot: {snapshot}")

        run(test, task, snapshot)
        yield test
