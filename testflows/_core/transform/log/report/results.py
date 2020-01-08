# Copyright 2019 Vitaliy Zakaznikov (TestFlows Test Framework http://testflows.com)
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
from testflows._core.transform.log import message
from testflows._core.transform.log.report.totals import Counts, all_counts
from testflows._core.transform.log.report.totals import format_test as process_test_counts
from testflows._core.transform.log.report.totals import format_result as process_result_counts

def process_test(msg, results):
    results["tests"][msg.name] = {"test": msg}
    process_test_counts(msg, results["counts"])

def process_result(msg, results):
    results["tests"][msg.test]["result"] = msg
    process_result_counts(msg, results["counts"])

def process_version(msg, results):
    results["version"] = msg.version
    results["started"] = msg.p_time

processors = {
    message.RawVersion: process_version,
    message.RawTest: process_test,
    message.RawResultOK: process_result,
    message.RawResultFail: process_result,
    message.RawResultError: process_result,
    message.RawResultSkip: process_result,
    message.RawResultNull: process_result,
    message.RawResultXOK: process_result,
    message.RawResultXFail: process_result,
    message.RawResultXError: process_result,
    message.RawResultXNull: process_result,
}

def transform(results, stop_event):
    """Transform parsed log line into a short format.
    """
    if results.get("tests") is None:
        results["tests"] = {}

    if results.get("counts") is None:
        results["counts"] = all_counts()

    line = None
    while True:
        if line is not None:
            processor = processors.get(type(line), None)
            if processor:
                processor(line, results)

        line = yield line