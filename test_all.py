#
# test_all.py
# A test suite that makes sure votes are being counted correctly
# Meant to be run with pytest: http://pytest.org
#
# To run this, install pytest and issue command:
# py.test
#

from src import util
from src import database
from src import votingspace

#
# Test the case where there is no tie.
#
def test_clear_winner():
    allVotes = [{"pref1": "Chipotle", "pref2": "NiMarcos", "pref3": "Ahipoki"},
                {"pref1": "Chipotle", "pref2": "La Santisima", "pref3": "The Hot Spot"},
                {"pref1": "1899", "pref2": "Chipotle", "pref3": "The Dub"}
                ]
    w = votingspace.determineWinner(allVotes)
    assert w == ["Chipotle", ["Chipotle"]]

#
# Test the case where there is a tie.
#
def test_tie():
    allVotes = [{"pref1": "Chipotle", "pref2": "NiMarcos", "pref3": "Ahipoki"},
                {"pref1": "NiMarcos", "pref2": "Chipotle", "pref3": "The Hot Spot"}
                ]
    w = votingspace.determineWinner(allVotes)
    assert "Chipotle" in w[1] and "NiMarcos" in w[1]

#
# Test the case where the winner is not what most voters had for their 1st pick
#
def test_winner_not_majority():
    allVotes = [{"pref1": "Chipotle", "pref2": "Huhot", "pref3": "Ahipoki"},
                {"pref1": "NiMarcos", "pref2": "Chipotle", "pref3": "The Hot Spot"},
                {"pref1": "Ahipoki", "pref2": "Chipotle", "pref3": "The Hot Spot"},
                {"pref1": "Karma", "pref2": "Hot Wok", "pref3": "Chipotle"}
                ]
    w = votingspace.determineWinner(allVotes)
    assert w == ["Chipotle", ["Chipotle"]]

