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
from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fd:
    long_description = fd.read()

setup(
    name="testflows.core",
    version="__VERSION__",
    description="TestFlows - Core",
    author="Vitaliy Zakaznikov",
    author_email="vzakaznikov@testflows.com",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/testflows/testflows-core",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.8",
    license="Apache-2.0",
    packages=[
        "testflows.core",
        "testflows.settings",
        "testflows._core",
        "testflows._core.contrib",
        "testflows._core.contrib.arpeggio",
        "testflows._core.contrib.markdown2",
        "testflows._core.contrib.pygments",
        "testflows._core.contrib.pygments.filters",
        "testflows._core.contrib.pygments.formatters",
        "testflows._core.contrib.pygments.lexers",
        "testflows._core.contrib.pygments.styles",
        "testflows._core.contrib.rsa",
        "testflows._core.contrib.pyasn1",
        "testflows._core.contrib.pyasn1.type",
        "testflows._core.contrib.pyasn1.compat",
        "testflows._core.contrib.pyasn1.codec",
        "testflows._core.contrib.pyasn1.codec.ber",
        "testflows._core.contrib.pyasn1.codec.cer",
        "testflows._core.contrib.pyasn1.codec.der",
        "testflows._core.contrib.pyasn1.codec.native",
        "testflows._core.contrib.yaml",
        "testflows._core.contrib.schema",
        "testflows._core.utils",
        "testflows._core.transform",
        "testflows._core.transform.log",
        "testflows._core.transform.log.report",
        "testflows._core.document",
        "testflows._core.document.new",
        "testflows._core.cli",
        "testflows._core.cli.arg",
        "testflows._core.cli.arg.handlers",
        "testflows._core.cli.arg.handlers.report",
        "testflows._core.cli.arg.handlers.report.compare",
        "testflows._core.cli.arg.handlers.transform",
        "testflows._core.cli.arg.handlers.document",
        "testflows._core.cli.arg.handlers.document.new",
        "testflows._core.cli.arg.handlers.requirement",
        "testflows._core.cli.arg.handlers.show"
        ],
    package_data={
        "testflows._core.document": ["*.css"],
        "testflows._core.document.new": ["*.md"],
    },
    scripts=[
        "testflows/_core/bin/tfs",
    ],
    zip_safe=False,
    install_requires=[
    ],
    extras_require={
        "dev": [
            "sphinx",
        ]
    }
)
