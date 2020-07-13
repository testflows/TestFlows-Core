# Copyright 2020 Katteli Inc.
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
import re

def human(l, key=None):
    """Sort in human readable format.

    Credit: https://blog.codinghorror.com/sorting-for-humans-natural-sort-order/
    :key: optional function to retrieve the key from the element
    """
    get_key = key
    if get_key is None:
        get_key = lambda x: x
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', get_key(key)) ]
    l.sort(key=alphanum_key)
    return l
