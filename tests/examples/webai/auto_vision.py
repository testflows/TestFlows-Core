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
# Based on https://github.com/andytyler/playwright-ai
# MIT License
#
# Copyright (c) 2024 Andy Tyler
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
import json

from contextlib import contextmanager

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from testflows.core import current, debug, When, And, Then, Step

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool


def screenshot(_cache={"count": 0}):
    """Take a screenshot of web browser screen.

    Returns: base64 encoded screenshot
    """
    driver: WebDriver = current().context.webdriver

    try:
        driver.save_screenshot(f"screenshots/screenshot_{_cache['count']}.png")
        screenshot_base64 = driver.get_screenshot_as_base64()
        _cache["count"] += 1
    except Exception as e:
        raise ValueError(f"Failed to make a screenshot: {e}")

    return screenshot_base64


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
def result_Action(result: bool) -> bool:
    """
    Handles the result of an action.

    This function is called at the end when the initial instructions asked to perform an action.

    Args:
        result (bool): True if action succeeded or False if the action failed..

    Returns:
        bool: returns the result.
    """
    try:
        return result
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


@tool
def take_screenshot() -> str:
    """
    Captures a screenshot of the current webpage.

    Returns:
        str: The screenshot bytes of the current webpage in JPEG format encoded as base64.
    """
    return screenshot()


@tool
def press_key(key: str) -> bool:
    """
    Simulates pressing a single key using pyautogui.

    Args:
        key (str): The key to press (e.g., "enter", "up", "a").

    Returns:
        bool: True if the action is successful, False if the key is not provided or an error occurs.
    """
    actions = ActionChains(current().context.webdriver)

    try:
        if not key:
            return False

        actions.send_keys(key).perform()
        return True
    except Exception as e:
        raise ValueError


@tool
def type_text(text: str) -> bool:
    """
    Simulates typing text using pyautogui.

    Args:
        text (str): The text to type.

    Returns:
        bool: True if the action is successful, False if the text is not provided.
    """
    actions = ActionChains(current().context.webdriver)

    try:
        if not text:
            return False

        actions.send_keys(text).perform()
        return True
    except Exception as e:
        raise ValueError(f"An error occurred while typing the text: {e}")


@tool
def mouse_move(coordinate: tuple) -> bool:
    """
    Moves the mouse to a specified position.

    Args:
        coordinate (tuple): A tuple of (x, y) representing the target coordinates.

    Returns:
        bool: True if the action is successful, False if the coordinate is invalid.
    """
    actions = ActionChains(current().context.webdriver)

    try:
        if not coordinate or len(coordinate) != 2:
            return False

        actions.w3c_actions.pointer_action.move_to_location(
            coordinate[0], coordinate[1]
        )
        actions.perform()

        return True
    except Exception as e:
        raise ValueError(f"An error occurred while moving the mouse: {e}")


@tool
def left_click(coordinate: tuple = (0, 0)) -> bool:
    """
    Simulates a left mouse click at the specified coordinates using pyautogui.

    Args:
        coordinate (tuple): A tuple of (x, y) representing the target coordinates. Defaults to (0, 0).

    Returns:
        bool: True if the action is successful, False if the coordinate is invalid.
    """
    actions = ActionChains(current().context.webdriver)

    try:
        if not coordinate or len(coordinate) != 2:
            return False

        actions.w3c_actions.pointer_action.move_to_location(
            coordinate[0], coordinate[1]
        )
        actions.click().perform()

        return True
    except Exception as e:
        raise ValueError(f"An error occurred while performing a left click: {e}")


@tool
def left_click_drag(start: tuple, end: tuple) -> bool:
    """
    Simulates a left mouse click and drag operation using pyautogui.

    Args:
        start (tuple): The starting coordinates as (x, y).
        end (tuple): The ending coordinates as (x, y).

    Returns:
        bool: True if the action is successful, False if coordinates are not provided.
    """
    actions = ActionChains(current().context.webdriver)

    try:
        # Validate that coordinates are provided
        if not start or not end or len(start) != 2 or len(end) != 2:
            return False

        # Move the mouse to the start position
        actions.w3c_actions.pointer_action.move_to_location(start[0], start[1])

        # Press the left mouse button
        actions.click_and_hold().perform()

        # Drag the mouse to the end position
        actions.w3c_actions.pointer_action.move_to_location(end[0], end[1])

        # Release the left mouse button
        actions.release().perform()

        return True
    except Exception as e:
        raise ValueError(f"An error occurred while performing left click drag: {e}")


@tool
def right_click(coordinate: tuple = (0, 0)) -> bool:
    """
    Simulates a right mouse click at the specified coordinates using pyautogui.

    Args:
        coordinate (tuple): A tuple of (x, y) representing the target coordinates. Defaults to (0, 0).

    Returns:
        bool: True if the action is successful, False if the coordinate is invalid.
    """
    actions = ActionChains(current().context.webdriver)

    try:
        # Validate that coordinates are provided
        if not coordinate or len(coordinate) != 2:
            return False

        # Move the mouse to the specified coordinate
        actions.w3c_actions.pointer_action.move_to_location(
            coordinate[0], coordinate[1]
        )

        # Perform a right-click at the current mouse position
        actions.context_click().perform()

        return True
    except Exception as e:
        raise ValueError(f"An error occurred while performing a right click: {e}")


@tool
def double_click(coordinate: tuple = (0, 0)) -> bool:
    """
    Simulates a double mouse click at the specified coordinates using pyautogui.

    Args:
        coordinate (tuple): A tuple of (x, y) representing the target coordinates. Defaults to (0, 0).

    Returns:
        bool: True if the action is successful, False if the coordinate is invalid.
    """
    try:
        if not coordinate or len(coordinate) != 2:
            return False

        # Move the mouse to the specified coordinates
        actions = ActionChains(current().context.webdriver)

        # Perform a double-click at the current mouse position
        actions.double_click().perform()

        return True
    except Exception as e:
        raise ValueError(f"An error occurred while performing a double click: {e}")


@tool
def coordinates(coordinates: dict[str, tuple]) -> bool:
    """Store a list of coordinates for elements

    Args:
        coordinates (dict[str, tuple]): A dictionary of element names and their coordinates.

    Returns:
        bool: True if the coordinates are stored successfully.
    """
    debug(f"Coordinates: {coordinates}")
    return True


tools = {
    "take_screenshot": take_screenshot,
    "press_key": press_key,
    "type_text": type_text,
    "mouse_move": mouse_move,
    "left_click": left_click,
    "left_click_drag": left_click_drag,
    "right_click": right_click,
    "double_click": double_click,
    "page_goto": page_goto,
    "expect_tobe": expect_toBe,
    "expect_nottobe": expect_notToBe,
    "coordinates": coordinates,
    # "result_assertion": result_Assertion,
    # "result_query": result_Query,
    "result_action": result_Action,
    "result_error": result_Error,
}


@tool
def chain_tool_calls(sequence: str) -> str:
    """
    Executes a sequence of tool calls sequentially.
    Use it  when each call does not need any arguments from the previous
    call.

    Args:
        sequence: A list of dictionaries in JSON format where:
            - "name" is the name of the tool to call.
            - "args" is the input for that tool.

    Returns:
        str: The output from the last executed tool in sequence.
    """
    sequence = json.loads(sequence)
    debug(f"Sequence: {sequence}")

    output = None

    for step in sequence:
        tool_name = step.get("name")
        tool_input = step.get("args", None)

        selected_tool = tools[tool_name]
        debug(f"Tool call: {tool_name}")
        try:
            output = selected_tool.invoke(tool_input)
        except Exception as e:
            output = str(e)
        debug(f"Tool output: {output}")

    return output


tools["chain_tool_calls"] = chain_tool_calls

llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)
llm_with_tools = llm.bind_tools(list(tools.values()))


def prompt(task):
    return f"""This is your task: {task}

Think step-by-step and provide your thoughts as you are executing a task.
"""


# Define the system prompt
system_message = SystemMessage(
    content="""You are autonomous agent that knowns how to interact with the web browser.
You look at screenshots, find the coordinates for all
the elements you need to interact with, and then you perform the actions
based on use tasks given to you.

You MUST use chain_tool_calls ALWAYS to speed up execution unless
it is not possible because you need an ouput from one tool to be passed to the next one.

For example: you can use chain_tool_calls in the following way:
* move_mouse, left_click, then type_text

The result_action and result_error MUST ALWAYS be called at the end.
Use result_error if the task cannot be completed or you've found an error.

You MUST keep your output to the MINIMUM.
You MUST only call the tools. Never provide any text. 
"""
)


def run(test, task, snapshot):
    """Execute AI task."""
    test.context.locator_map = {}

    messages = [
        system_message,
        HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": f"{prompt(task)}",
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": snapshot,
                    },
                },
            ]
        ),
    ]

    ai_msg = llm_with_tools.invoke(messages)
    debug(f"{ai_msg}")

    while ai_msg.tool_calls:
        messages.append(ai_msg)
        for tool_call in ai_msg.tool_calls:
            tool_name = tool_call["name"].lower()
            selected_tool = tools[tool_name]
            args = tool_call["args"]
            debug(f"Tool call: {tool_call}")
            try:
                tool_output = selected_tool.invoke(args)
            except Exception as e:
                tool_output = str(e)
            debug(f"Tool output: {tool_output}")

            if tool_name == "take_screenshot":
                debug("Returning screenshot")
                messages.append(
                    ToolMessage(
                        "",
                        artifact={
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": tool_output,
                            },
                        },
                        tool_call_id=tool_call["id"],
                    )
                )
            else:
                messages.append(ToolMessage(tool_output, tool_call_id=tool_call["id"]))

        ai_msg = llm_with_tools.invoke(messages)

    messages.append(ai_msg)
    debug(f"{ai_msg}")


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
        snapshot = screenshot()
        run(test, task, snapshot)

        yield test
