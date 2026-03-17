import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from logic_utils import check_guess


def test_guess_below_minimum_is_too_low():
    # guess=1, secret=50: 1 is below the secret, must hint Go HIGHER!
    outcome, message = check_guess(1, 50)
    assert outcome == "Too Low"
    assert "HIGHER" in message


def test_guess_above_maximum_is_too_high():
    # guess=100, secret=50: 100 is above the secret, must hint Go LOWER!
    outcome, message = check_guess(100, 50)
    assert outcome == "Too High"
    assert "LOWER" in message


def test_exact_guess_is_win():
    # guess=50, secret=50: exact match must be a win
    outcome, message = check_guess(50, 50)
    assert outcome == "Win"
    assert "Correct" in message
