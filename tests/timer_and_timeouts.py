import time
from testflows.core import *
from testflows.asserts import error, raises


@TestSketch(Scenario)
def combinations(self):
    """Check different combination of options."""

    timeout = either(None, 0.1, 0.25, 0.6)
    message = either(None, "hello")
    started = either(None, 0, time.time() + 10, self.start_time)
    delay = either(0, 0.5)
    loops = either(1, 2)

    with Check(
        f"timeout={timeout},message={message},started={started},delay={delay},loops={loops}"
    ):
        timer = Timer(timeout=timeout, message=message, started=started)

        for i in range(loops):
            timeout_expected = timeout and (time.time() - timer.started) >= timeout
            with raises(TimeoutError if timeout_expected else None):
                try:
                    with timer:
                        time.sleep(delay / loops)
                    with Then("check elapsed time is within expected range"):
                        assert (
                            timer.elapsed - (time.time() - timer.started) < 0.01
                        ), error()
                except TimeoutError as err:
                    with Then("check TimeoutError message"):
                        note(f"TimeoutError: {err}")
                        if not message:
                            assert str(err) == f"timeout {timer.timeout}s", error()
                        else:
                            assert (
                                str(err) == f"timeout {timer.timeout}s: {message}"
                            ), error()
                    raise


@TestSuite
def timers(self):
    """Check timers."""

    with Scenario("stopwatch"):
        with timer() as stopwatch:
            with Then("check elapsed property returns a float"):
                assert type(stopwatch.elapsed) is float, error()

            with And("check elapsed property is < 1 and > 0"):
                debug(stopwatch.elapsed)
                assert 1 > stopwatch.elapsed > 0, error()

            with And("check elapsed time increases"):
                time.sleep(1)
                assert stopwatch.elapsed > 1, error()

        with Then(
            "check elapsed property value is fixed after timer context manager exits"
        ):
            elapsed = stopwatch.elapsed
            time.sleep(0.2)
            assert elapsed == stopwatch.elapsed, error()

    with Scenario("stopwatch with future started time"):
        with timer(started=time.time() + 100) as stopwatch:
            with Then("check elapsed is negative"):
                debug(stopwatch.elapsed)
                assert -99 > stopwatch.elapsed > -100, error()
                time.sleep(1)
                assert -98 > stopwatch.elapsed > -99, error()

    with Scenario("stopwatch using scenario start time as started"):
        stopwatch = Timer(started=current().start_time)
        for i in range(2):
            with Then("check stopwatch.elapsed is close to current test time #{i}"):
                debug(current_time() - stopwatch.elapsed)
                assert current_time() - stopwatch.elapsed < 2**-6, error()
                time.sleep(0.2)

    with Scenario("reusing stopwatch"):
        stopwatch = Timer()

        with When("I use the stopwatch for the first time"):
            with stopwatch:
                pass

        with And("I save the elapsed time"):
            elapsed = stopwatch.elapsed

        with When("I reuse the stopwatch"):
            with stopwatch:
                pass

        with Then("elapsed time is updated"):
            assert elapsed != stopwatch.elapsed, error()

    Scenario(run=combinations)


@TestScenario
@Timeouts(Timeout(0.1, name="first timeout"), Timeout(0.2, name="second timeout"))
@Flags(EFAIL)
def test_with_timeouts(self):
    for i in range(12):
        with By(f"sleeping {i} time"):
            time.sleep(0.01)


@TestScenario
@Timeout(0.1, message="custom message", name="first timeout")
@Flags(EFAIL)
def test_with_timeout(self):
    for i in range(12):
        with By(f"sleeping {i} time"):
            time.sleep(0.01)


@TestFeature
def timeouts(self):
    """Check timeouts."""
    with Scenario("parent with timeout"):
        with Check("check with timeout", timeouts=[Timeout(0.1)], flags=EFAIL):
            for i in range(12):
                with By(f"sleeping {i} time"):
                    time.sleep(0.01)

    with Scenario("inner timeout fail"):
        with Check("check with timeout", timeouts=[Timeout(3)], flags=EFAIL):
            for i in range(12):
                with By(f"step {i}", timeouts=[Timeout(0.1, started=current().start_time)]):
                    time.sleep(0.01)

    with Scenario("outer timeout fail"):
        with Check("check with timeout", timeouts=[Timeout(0.3)], flags=EFAIL):
            for i in range(12):
                with By(f"step {i}", timeouts=[Timeout(3)]):
                    time.sleep(0.1)

    with Scenario("three timeouts"):
        with Check("first", timeouts=[Timeout(0.3)], flags=EFAIL):
            with By("doing something", timeouts=[Timeout(2)]):
                for i in range(12):
                    with By(f"step {i}", timeouts=[Timeout(3)]):
                        time.sleep(0.1)

        with Check("second", timeouts=[Timeout(3)], flags=EFAIL):
            with By("doing something", timeouts=[Timeout(0.1)]):
                for i in range(12):
                    with By(f"step {i}", timeouts=[Timeout(3)]):
                        time.sleep(0.1)

        with Check("third", timeouts=[Timeout(3)], flags=EFAIL):
            with By("doing something", timeouts=[Timeout(2)]):
                for i in range(12):
                    with By(f"step {i}", timeouts=[Timeout(0.1, started=current().start_time)]):
                        time.sleep(0.1)

    with Scenario("with started time"):
        with Check(
            "check fail", timeouts=[Timeout(0.1, started=time.time())], flags=EFAIL
        ):
            for i in range(2):
                with By(f"iteration {i}"):
                    time.sleep(0.1)

        with Check("check pass", timeouts=[Timeout(0.1, started=time.time() + 1)]):
            for i in range(2):
                with By(f"iteration {i}"):
                    time.sleep(0.1)

    with Scenario("with name"):
        with Check(
            "check with timeout",
            timeouts=[Timeout(0.1, name="max operation time")],
            flags=EFAIL,
        ):
            for i in range(2):
                with By(f"iteration {i}"):
                    time.sleep(0.1)

    with Scenario("with message"):
        with Check(
            "check with timeout",
            timeouts=[Timeout(0.1, message="custom message")],
            flags=EFAIL,
        ) as check:
            for i in range(2):
                with By(f"iteration {i}"):
                    time.sleep(0.1)

        assert "custom message" in check.result.message, error()

    with Scenario("with message and name"):
        with Check(
            "check with timeout",
            timeouts=[Timeout(0.1, message="custom message", name="custom name")],
            flags=EFAIL,
        ) as check:
            for i in range(2):
                with By(f"iteration {i}"):
                    time.sleep(0.1)

        assert "custom name: custom message" in check.result.message, error()

    with Scenario("non float timeout"):
        with raises(ValueError):
            with Check("check with timeout", timeouts=[Timeout("hello")]):
                pass

    with Scenario("timeout <= 0"):
        with raises(ValueError):
            with Check("check with timeout", timeouts=[Timeout(0)]):
                pass

        with raises(ValueError):
            with Check("check with timeout", timeouts=[Timeout(-1)]):
                pass

    with Scenario("started >= 0"):
        with Check("check with timeout", timeouts=[Timeout(1, started=0)], flags=EFAIL):
            pass

        with raises(ValueError):
            with Check("check with timeout", timeouts=[Timeout(1, started=-1)]):
                pass

    with Scenario(
        "using xargs",
        xargs={"check with timeout": [{"timeouts": [Timeout(0.1)], "flags": EFAIL}]},
    ):
        with Check("check with timeout", flags=EFAIL):
            for i in range(12):
                with By(f"sleeping {i} time"):
                    time.sleep(0.01)

    with Feature("decorated tests"):
        Scenario(run=test_with_timeouts)
        Scenario(run=test_with_timeout)


@TestFeature
@Name("timer and timeouts")
def feature(self):
    """Regression tests for timer and timeouts."""
    Feature("timer", run=timers)
    Feature("timeouts", run=timeouts)


if main():
    feature()
