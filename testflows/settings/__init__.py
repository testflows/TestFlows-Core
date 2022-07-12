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
import uuid
import hashlib

#: debug mode
debug = False
#: time resolution (decimal places)
time_resolution = 6
#: hash length in bytes
hash_length = 8
#: hash function
hash_func = hashlib.sha1
#: disable cli colors
no_colors = False
#: test id
test_id = str(uuid.uuid1())
#: output handler format
output_format = None
#: log file
write_logfile = None
read_logfile = None
#: database
database = None
#: show skipped tests
show_skipped = False
#: show retries
show_retries = False
#: show trimmed result messages
trim_results = True
#: randomize order of loaded tests
random_order = False
#: global thread pool
global_thread_pool = None
#: global async pool
global_async_pool = None
#: global process pool
global_process_pool = None
#: service timeout
service_timeout = 0.1
#: secrets registry
secrets_registry = None
#: tracing
trace = False
