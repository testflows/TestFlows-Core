# Copyright 2021 Katteli Inc.
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
from testflows._core.parallel import Context, ContextVar, copy_context
from testflows._core.parallel.executor.thread import ThreadPoolExecutor as Pool, ThreadPoolExecutor as ThreadPool
from testflows._core.parallel.executor.thread import SharedThreadPoolExecutor as SharedPool, SharedThreadPoolExecutor as SharedThreadPool
from testflows._core.parallel.executor.asyncio import AsyncPoolExecutor as AsyncPool, SharedAsyncPoolExecutor as SharedAsyncPool
from testflows._core.parallel.executor.process import ProcessPoolExecutor as ProcessPool, SharedProcessPoolExecutor as SharedProcessPool, process_service
