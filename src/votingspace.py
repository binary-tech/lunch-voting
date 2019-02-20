#
# votingspace
# The place where users go to cast votes and view the results
#

from flask import render_template
from flask import url_for
from flask import session
from flask import request
from flask import Blueprint
from flask import flash
from flask import redirect
votingspace_api = Blueprint('votingspace_api', __name__)

import os
import arrow      # date/time library
import random

import re
from . import util
from . import database

from flask import current_app
from flask import g

from time import sleep

@votingspace_api.route("/s/<spacestring>", methods=["GET", "POST"])
def votingspace(spacestring):

    # set up named constants that indicate what step we are currently on
    START = 0           # just display the user interface for submitting a vote
    JUST_VOTED = 1      # a new vote was just recorded in the database
    NO_ELECTION = 2     # there are no elections for today
    OFFER_NEW_SPACE = 3 # there is no such voting space, offer to make a new one

    if request.method == "GET":

        # default to (no preference) for every preference
        if 'pref1' not in session:
            session['pref1'] = None
        if 'pref2' not in session:
            session['pref2'] = None
        if 'pref3' not in session:
            session['pref3'] = None

        # get information about the current date
        now = arrow.now()
        nowHMS = now.format("HH:mm:ss").split(":")
        nowAsSeconds = int(nowHMS[0])*60*60 + int(nowHMS[1])*60 + int(nowHMS[2])
        today = now.format("YYYY-MM-DD")           # 4 digit year - 0 padded month - 0 padded day, psql's default format
        todayReadable = now.format("MMMM D, YYYY") # month name, day of month, 4 digit year

        # determine whether or not to show the "start a new election" button
        morning = now.replace(hour=8, minute=0, second=0)
        evening = now.replace(hour=19, minute=0, second=0)
        showStartElectionBtn = (now >= morning and now <= evening)

        # offer to make a voting space if the requested one does not exist
        electionsToday = database.getElectionsOnDay(today, spacestring)
        if electionsToday == None:
            params = {
                'action': OFFER_NEW_SPACE,
                'urlForFeedback': url_for("feedback_api.feedback"),
                'spacestring': spacestring,

                'OFFER_NEW_SPACE': 3
            }
            return render_template("votingspace.html", **params)

        # let the user set up a new election if no elections are scheduled for today
        if (len(electionsToday) == 0):
            params = {
                'action': NO_ELECTION,
                'urlForFeedback': url_for("feedback_api.feedback"),
                'showStartElectionBtn': showStartElectionBtn,
                'urlForStartElection': url_for("startelection_api.startelection", spacestring=spacestring),
                'urlForAddContact': url_for("addcontact_api.addcontact", spacestring=spacestring),
                'urlForListPlaces': url_for("listplaces_api.listplaces", spacestring=spacestring),
                'urlForAdmin': url_for("admin_api.admin", spacestring=spacestring),

                'NO_ELECTION': 2
            }
            return render_template("votingspace.html", **params)

        # we now know that there is a election for today; figure out when voting closes because we need that information
        # three possibilities:
            # we are rendering the page for the first time
            # we are redirecting back here from a POST request after submitting a vote
            # we are rendering this page after voting has closed and need to show results

        vote_end_db = str(electionsToday[0]['timevotingends'])
        electionIdForTmpl = electionsToday[0]['id']

        # create a date object for the moment voting ends of the form: date_create("2014:04:26 13:01:02")
        vote_end = now.replace(hour=int(vote_end_db.split(":")[0]), minute=int(vote_end_db.split(":")[1]), second=0)
        voteEndHMS = vote_end.format("HH:mm:ss").split(":")
        voteEndAsSeconds = int(voteEndHMS[0])*60*60 + int(voteEndHMS[1])*60 + int(voteEndHMS[2])
        intervalToVoteClose = arrow.get(vote_end).humanize()
        voteEndReadable = "{}:{}".format(vote_end_db.split(":")[0], vote_end_db.split(":")[1])
        secondsToClose = voteEndAsSeconds - nowAsSeconds + 1

        # show results if voting has closed by now
        if (now >= vote_end):
            params = getResultsParams(spacestring)
            return render_template("votingspace.html", **params)

        # show the voting confirmation page if the POST request from having just voted redirected us here
        if "action" in request.args and int(request.args["action"]) == JUST_VOTED:
            voteKey = None if ("voteKey" not in request.args) else request.args["voteKey"]
            electionId = None if ("electionId" not in request.args) else request.args["electionId"]
            pref1 = None if ("pref1" not in request.args) else request.args["pref1"]
            pref2 = None if ("pref2" not in request.args) else request.args["pref2"]
            pref3 = None if ("pref3" not in request.args) else request.args["pref3"]
            params = {
                'action': JUST_VOTED,
                'urlForFeedback': url_for("feedback_api.feedback"),
                'voteKey': voteKey,
                'electionId': electionId,
                'intervalToVoteClose': intervalToVoteClose,
                'secondsToClose': secondsToClose,
                'voteEndReadable': voteEndReadable,
                'nameOfPref1': database.getNameById(pref1, 'venues', spacestring),
                'nameOfPref2': database.getNameById(pref2, 'venues', spacestring),
                'nameOfPref3': database.getNameById(pref3, 'venues', spacestring),
                'urlForAdmin': url_for("admin_api.admin", spacestring=spacestring),
                'urlForVotingSpace': url_for("votingspace_api.votingspace", spacestring=spacestring),

                'JUST_VOTED': 1
            }

            return render_template("votingspace.html", **params)

        # we now know that we are rendering this page for the first time and must present the user with voting options

        # add indicators to venue names that show they have been voted for today
        votedForSoFar = database.getUniqueVotes(electionIdForTmpl)
        venueList = database.getOpenVenues(spacestring)
        for venue in venueList:
            if venue[0] in votedForSoFar:
                venueList[venueList.index(venue)] = [venue[0], "[ V ] " + str(venue[1])]

        # count the number of votes cast so far in this election
        voteCount = len(util.toDicts(database.getVotes(electionIdForTmpl)))

        # make a human-readable string for the current vote count, such as "3 votes"
        voteCountDesc = "{} votes".format(voteCount)
        if voteCount == 1:
            voteCountDesc = "1 vote"

        # assign a css class to the string reporting the number of votes counted;
        #   needs to stand out if not enough votes are in yet
        voteCountDescClass = ""
        if voteCount < g.minVoteCount:
            voteCountDescClass = "urgentVoteCountDesc"

        params = {
            'action': START,    # by default, render the first step by asking the user for a new vote
            'urlForFeedback': url_for("feedback_api.feedback"),
            'query': electionsToday[0]['query'],
            'formAction': url_for("votingspace_api.votingspace", spacestring=spacestring),
            'urlForAddContact': url_for("addcontact_api.addcontact", spacestring=spacestring),
            'urlForAddPlace': url_for("addplace_api.addplace", spacestring=spacestring),
            'intervalToVoteClose': intervalToVoteClose,
            'secondsToClose': secondsToClose,
            'voteEndReadable': voteEndReadable,
            'minVoteCount': g.minVoteCount,
            'voteCount': voteCount,
            'voteCountDesc': voteCountDesc,
            'voteCountDescClass': voteCountDescClass,
            'venueList': venueList,
            'electionId': electionIdForTmpl,
            'today': today,
            'todayReadable': todayReadable,
            'oneOffMessages': database.getOneOffMessages(),
            'urlForAdmin': url_for("admin_api.admin", spacestring=spacestring),

            'START': 0
        }

        return render_template("votingspace.html", **params) # unpack the params dictionary, using its values as named parameters

    elif request.method == "POST":

        data = request.form
        electionId = int(data["electionId"])
        pref1 = int(data["pref1"])
        pref2 = int(data["pref2"])
        pref3 = int(data["pref3"])
        voteKey = str(data["voteKey"]).upper()
        voteToEdit = database.getVoteForKey(voteKey)
        editCheckbox = (data.getlist("editCheckbox") == ["on"])    # true if "edit previous vote" checkbox as checked

        # -1 signifies a preference of (no preference), so convert those to None
        pref1 = None if (pref1 == -1) else pref1
        pref2 = None if (pref2 == -1) else pref2
        pref3 = None if (pref3 == -1) else pref3

        # remember user's selections, which is helpful when coming back to edit a vote
        session["pref1"] = pref1
        session["pref2"] = pref2
        session["pref3"] = pref3

        # check for preferences that appear multiple times in the same vote
        if (((pref1 != None) and pref1 == pref2) or
           ((pref2 != None) and pref2 == pref3) or
           ((pref1 != None) and pref1 == pref3)):
            flash("Error: Cannot specify the same option in multiple positions", "error")
            return redirect(url_for('.votingspace', spacestring=spacestring))

        # check for attempts to edit non-existent votes
        if editCheckbox and voteToEdit == -1:
            flash("Error: No vote for key {}".format(voteKey), "error")
            return redirect(url_for('.votingspace', spacestring=spacestring))

        # check for attempts to edit vote for an election that has ended
        if editCheckbox and database.voteKeyHasExpired(voteKey):
            flash("Error: Key {} no longer valid".format(voteKey), "error")
            return redirect(url_for('.votingspace', spacestring=spacestring))

        # if a valid vote key has been passed, edit a vote instead of casting a new one
        if not editCheckbox:
            newVoteId = database.recordVote(electionId, (pref1, pref2, pref3)) # cast a new vote
            voteKey = database.generateKey()
            database.setVoteKey(newVoteId, voteKey)
            flash("Vote added successfully", "success")
        else:
            database.updateVote(voteToEdit, (pref1, pref2, pref3)) # edit an existing vote
            flash("Vote edited successfully", "success")

        params = {
            'action': JUST_VOTED,
            'voteKey': voteKey,       # either a valid key entered by a user trying to edit a vote, or a newly generated key
            'electionId': electionId,
            'pref1': pref1,
            'pref2': pref2,
            'pref3': pref3,
            'spacestring': spacestring
        }

        # don't render a template directly off of a POST request; redirect to a GET request, avoiding problems if the user manually reloads the page
        return redirect(url_for('.votingspace', **params))

#
# Get parameters for rendering results
#
def getResultsParams(spacestring):

    SHOW_RESULTS = 3
    TOO_FEW_ERROR = 6

    # by default, only display the user interface
    action = SHOW_RESULTS

    # show an error message if no elections are scheduled for today
    now = arrow.now()
    today = now.format("YYYY-MM-DD") # 4 digit year - 0 padded month - 0 padded day, psql's default format

    overallWinner = ""
    electionsToday = database.getElectionsOnDay(today, spacestring)
    tieList = []
    oneOffMessages = database.getOneOffMessages()
    query = electionsToday[0]['query']

    # calculate how long it will be before voting ends and results will be ready
    electionId = electionsToday[0]['id']

    allVotes = util.toDicts(database.getVotes(electionId))

    # add fields "pref1", "pref2", "pref3" to allVotes, which store ranked preferences for each vote
    for i, vote in enumerate(allVotes):
        prefs = [n['venueid'] for n in database.getPrefs(vote['id'])]
        allVotes[i]['pref1'] = prefs[0]
        allVotes[i]['pref2'] = prefs[1]
        allVotes[i]['pref3'] = prefs[2]

    # make an array of vote names
    allVoteNames = []
    for vote in allVotes:
        votePrefs = database.getPrefs(vote['id'])
        votePrefNames = [database.getNameById(i['venueid'], 'venues', spacestring) for i in votePrefs]
        allVoteNames.append(votePrefNames)

    if len(allVotes) < 4:
        action = TOO_FEW_ERROR
    else:

        overallWinnerId = -1
        if len(allVotes) > 0:
            winnerResults = determineWinner(allVotes)
            overallWinnerId = winnerResults[0]
            overallWinner = database.getNameById(overallWinnerId, 'venues', spacestring)
            tieList = [database.getNameById(i, 'venues', spacestring) for i in winnerResults[1]]

        # record this newly calculated result as the new winner, if current winner is null
        winnerInDb = database.getWinnerForElection(electionId)
        if winnerInDb == None:
            if overallWinnerId != -1:
                database.recordWinner(electionId, overallWinnerId)

                # send out messages to subscribed users letting them know the result
                targetEmails = database.getResultsEmailAddresses(spacestring)
                for email in targetEmails:
                    sleep(.1)
                    util.sendEmail(email, "The prevailing option is {}".format(overallWinner))

        else:
            overallWinnerId = winnerInDb  # otherwise, overwrite the result just calculated with what's in the database
            overallWinner = database.getNameById(overallWinnerId, 'venues', spacestring)

    params = {
        'title': 'page title',
        'urlForFeedback': url_for("feedback_api.feedback"),
        'action': action,
        'today': today,
        'query': query,
        'oneOffMessages': oneOffMessages,
        'overallWinner': overallWinner,
        'tieList': tieList,
        'allVoteNames': allVoteNames,
        'urlForVotingSpace': url_for("votingspace_api.votingspace", spacestring=spacestring),
        'urlForListPlaces': url_for("listplaces_api.listplaces", spacestring=spacestring),
        'urlForAdmin': url_for("admin_api.admin", spacestring=spacestring),

        'SHOW_RESULTS': 3,
        'TOO_FEW_ERROR': 6
    }

    return params

#
# Find a list of the form: [overall winner randomly selected from best options, [list of best options]]
#
def determineWinner(allVotes):
    tallies = bordaCount(allVotes)
    possibleWinners = findPossibleWinners(tallies)
    if len(possibleWinners) == 0:
        return [None, possibleWinners]
    return [random.choice(possibleWinners), possibleWinners]

#
# Use the Borda count method to produce tallies
#
def bordaCount(allVotes):
    tallies = {}
    for vote in allVotes:
        if vote['pref1'] not in tallies:
            tallies[vote['pref1']] = 0
        tallies[vote['pref1']] += 3

        if vote['pref2'] not in tallies:
            tallies[vote['pref2']] = 0
        tallies[vote['pref2']] += 2

        if vote['pref3'] not in tallies:
            tallies[vote['pref3']] = 0
        tallies[vote['pref3']] += 1

    return tallies

#
# Find the maximum borda count of any option
#
def findMaxTally(tallies):
    result = -1
    for name, tally in tallies.items():
        if tally > result and name != None:   # None means (no preference) and cannot win
            result = tally
    return result

#
# Find all the potentially winning options, returned as a list of names
#
def findPossibleWinners(tallies):
    result = []
    m = findMaxTally(tallies)
    for name, tally in tallies.items():
        if tally == m and name != None:       # None means (no preference) and cannot win
            result.append(name)
    return result
