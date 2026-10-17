"""Tests for the decision logic. Run with: python -m pytest tests/ -v"""
import os
import sys

# Let the tests import from src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from decision import Decider  # noqa: E402


def test_starts_idle():
    d = Decider()
    assert d.update(False, now=0.0) == "IDLE"


def test_two_hits_is_not_enough():
    d = Decider()
    d.update(True, now=0.0)
    d.update(True, now=0.1)
    assert d.update(False, now=0.2) == "IDLE"


def test_three_hits_in_five_frames_triggers_alert():
    d = Decider()
    for t, hit in enumerate([True, False, True, False, True]):
        state = d.update(hit, now=t * 0.1)
    assert state == "ALERT"


def test_alert_holds_then_clears():
    d = Decider()
    for t in range(3):
        d.update(True, now=t * 0.1)          # trigger the alert at t=0.2
    # Misses for a while: still ALERT inside the 5-second hold
    assert d.update(False, now=3.0) == "ALERT"
    # After the hold with no new hits, it returns to IDLE
    for i in range(10):
        state = d.update(False, now=3.0 + i)
    assert state == "IDLE"


def test_old_hits_fall_out_of_window():
    d = Decider()
    d.update(True, now=0.0)
    d.update(True, now=0.1)
    for t in range(2, 7):                    # push the two hits out of the window
        d.update(False, now=t * 0.1)
    assert d.update(True, now=1.0) == "IDLE"


def test_miss_frames_do_not_extend_hold():
    d = Decider()
    for t in [0.0, 0.1, 0.2]:                # alert starts; last hit is at 0.2
        d.update(True, now=t)
    for t in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
        d.update(False, now=t)               # misses should not move the hold timer
    # Hold ends 5 s after the last HIT (0.2), so 5.1 is still ALERT and 5.3 is IDLE
    assert d.update(False, now=5.1) == "ALERT"
    assert d.update(False, now=5.3) == "IDLE"
