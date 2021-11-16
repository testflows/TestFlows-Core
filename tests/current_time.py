import time
from testflows.core import *

with Scenario("my test"):
    with Step("my step") as step:
        note(current_time())
        time.sleep(1)
        note(current_time())

    note(step.test_time)
    note(current_time(test=step))

    assert current_time(test=step) == step.test_time
