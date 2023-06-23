import json
import functools
from testflows.core import *

with Scenario("test"):
    with Given("I create engines list for current test"):
        engines = define(
            "engines",
            [
                "ReplacingMergeTree",
                "AggregatingMergeTree",
                "SummingMergeTree",
                "MergeTree",
                "StripeLog",
                "TinyLog",
                "Log",
            ],
            encoder=lambda s: ", ".join(s),
        )

    with Given("I create statements with and without `FINAL`."):
        query = define(
            "query without FINAL", "SELECT count() FROM {name} FORMAT JSONEachRow;"
        )
        query_with_final = define(
            "query with FINAL", "SELECT count() FROM {name} {final} FORMAT JSONEachRow;"
        )
