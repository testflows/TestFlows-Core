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
from testflows._core.name import parentname
from testflows._core.message import Message
from testflows._core.transform.log.report.totals import Counts, all_counts
from testflows._core.transform.log.report.totals import format_test as process_test_counts
from testflows._core.transform.log.report.totals import format_result as process_result_counts

def process_test(msg, results, names, unique):
    def add_name(name, names, unique, test_id):
        _name = name
        duplicate = 0
        if name in unique:
            duplicate = unique[name]
            duplicate += 1
            _name = f'{name} ~{duplicate}'
        names[test_id] = _name
        unique[name] = duplicate
        return

    add_name(msg["test_name"], names, unique, msg["test_id"])
    test = {
        "attributes":[], "arguments":[], "tags": [],
        "specifications": [], "requirements": [],
        "node": None, "map": [], "examples": []
    }
    test.update(msg)
    results["tests"][names[msg["test_id"]]] = {"test": test, "result": {"tickets":[], "values":[], "metrics":[]}}
    process_test_counts(msg, results["counts"])

    # add test to the tests map
    parent = parentname(msg["test_id"])
    if results["tests_by_parent"].get(parent) is None:
        results["tests_by_parent"][parent] = []
    results["tests_by_parent"][parent].append(test)
    results["tests_by_id"][msg["test_id"]] = test

def process_result(msg, results, names, unique):
    results["tests"][names[msg["test_id"]]]["result"].update(msg)
    process_result_counts(msg, results["counts"])

def process_version(msg, results, names, unique):
    results["version"] = msg["framework_version"]
    results["started"] = msg["message_time"]

def process_protocol(msg, results, names, unique):
    results["protocol"] = msg["protocol_version"]

def process_attribute(msg, results, names, unique):
    results["tests"][names[msg["test_id"]]]["test"]["attributes"].append(msg)

def process_tag(msg, results, names, unique):
    results["tests"][names[msg["test_id"]]]["test"]["tags"].append(msg)

def process_requirement(msg, results, names, unique):
    results["tests"][names[msg["test_id"]]]["test"]["requirements"].append(msg)

def process_specification(msg, results, names, unique):
    results["specifications"].append(msg)
    results["tests"][names[msg["test_id"]]]["test"]["specifications"].append(msg)

def process_argument(msg, results, names, unique):
    results["tests"][names[msg["test_id"]]]["test"]["arguments"].append(msg)

def process_example(msg, results, names, unique):
    results["tests"][names[msg["test_id"]]]["test"]["examples"].append(msg)

def process_node(msg, results, names, unique):
    results["tests"][names[msg["test_id"]]]["test"]["node"] = msg

def process_map(msg, results, names, unique):
    results["tests"][names[msg["test_id"]]]["test"]["map"].append(msg)

def process_ticket(msg, results, names, unique):
    results["tests"][names[msg["test_id"]]]["result"]["tickets"].append(msg)

def process_metric(msg, results, names, unique):
    results["tests"][names[msg["test_id"]]]["result"]["metrics"].append(msg)

def process_value(msg, results, names, unique):
    results["tests"][names[msg["test_id"]]]["result"]["values"].append(msg)

processors = {
    Message.VERSION.name: process_version,
    Message.PROTOCOL.name: process_protocol,
    Message.TEST.name: process_test,
    Message.RESULT.name: process_result,
    Message.ATTRIBUTE.name: process_attribute,
    Message.TAG.name: process_tag,
    Message.SPECIFICATION.name: process_specification,
    Message.REQUIREMENT.name: process_requirement,
    Message.ARGUMENT.name: process_argument,
    Message.EXAMPLE.name: process_example,
    Message.NODE.name: process_node,
    Message.MAP.name: process_map,
    Message.TICKET.name: process_ticket,
    Message.METRIC.name: process_metric,
    Message.VALUE.name: process_value,
}

def transform(results):
    """Transform log file into results.
    """
    names = {}
    # unique test names
    unique = {}

    if results.get("tests") is None:
        results["tests"] = {}

    if results.get("tests_by_parent") is None:
        results["tests_by_parent"] = {}

    if results.get("tests_by_id") is None:
        results["tests_by_id"] = {}

    if results.get("counts") is None:
        results["counts"] = all_counts()

    if results.get("started") is None:
        results["started"] = 0

    if results.get("version") is None:
        results["version"] = ""

    if results.get("specifications") is None:
        results["specifications"] = []

    line = None
    while True:
        if line is not None:
            processor = processors.get(line["message_keyword"], None)
            if processor:
                processor(line, results, names, unique)

        line = yield line
