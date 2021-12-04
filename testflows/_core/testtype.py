# Copyright 2019 Katteli Inc.
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
from .utils.enum import IntEnum

class TestType(IntEnum):
    """Test type."""
    Module = 40
    Suite = 30
    Test = 20
    Outline = 17
    Iteration = 15
    RetryIteration = 14
    Step = 10

class TestSubType(IntEnum):
    """Test behaviour subtype."""
    Book = 70
    Feature = 60
    Chapter  = 55
    Scenario = 50
    Document = 48
    Section = 47
    Page = 46
    Example = 45
    Background = 40
    Recipe = 35
    Critical = 34
    Check = 33
    Major = 32
    Minor = 31
    Given = 30
    Paragraph = 25
    When = 20
    Then = 10
    And = 8
    But = 7
    By = 6
    Finally = 5
    Cleanup = 4
