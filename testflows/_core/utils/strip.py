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

def wstrip(s, word, left=True, right=True):
    """Strip word from the beginning or the end of the string.
    By default strips from both sides.
    """
    step = len(word)
    start_pos = None
    end_pos = None

    if not word:
        return s

    while True:
        found = False
        if left and s.startswith(word, start_pos, end_pos):
            if start_pos is None:
                start_pos = 0
            start_pos += step
            found = True
        if right and s.endswith(word, start_pos, end_pos):
            if end_pos is None:
                end_pos = 0
            end_pos -= step
            found = True
        if not found:
            break

    return s[start_pos:end_pos]

def lwstrip(s, word):
    """Strip word only from the left side.
    """
    return wstrip(s, word, right=False)

def rwstrip(s, word):
    """Strip word only from the right side.
    """
    return wstrip(s, word, left=False)