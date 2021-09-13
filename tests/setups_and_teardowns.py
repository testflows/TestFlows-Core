#!/usr/bin/env python3
from testflows.core import *
from testflows.asserts import error, values

@TestBackground
def open_logs(self):
     with Given("open log1"):
         self.append(open("helllo", "w+"))
     with Given("open log2"):
         self.append(open("helllo2", "w+"))
     yield self
     with Finally("I close the logs"):
         pass

@TestFeature
def background(self):
    """Check using Background test definition 
    and TestBackground decorator.
    """
    with Scenario("direct call"):
        log, log2 = open_logs()
        assert log.closed is False and log2.closed is False, error()
    assert log.closed is True and log2.closed is True, error()

    with Scenario("run test definition"):
        log, log2 = Background(run=open_logs)
        assert log.closed is False and log2.closed is False, error()
    assert log.closed is True and log2.closed is True, error()
   
    with Scenario("direct call inside test definition"): 
        with Background("open logs"): # works
            log, log2 = open_logs()
        assert log.closed is False and log2.closed is False, error()
    assert log.closed is True and log2.closed is True, error()
        
    with Scenario("call test definition"):
        log, log2 = Background(test=open_logs)()
        assert log.closed is False and log2.closed is False, error()
    assert log.closed is True and log2.closed is True, error()

if main():
    background()
