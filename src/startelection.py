#
# admin
# The page for administrators to do admin things such as add elections
#

from flask import render_template
from flask import url_for
from flask import session
from flask import request
from flask import Blueprint
from flask import flash
from flask import redirect
startelection_api = Blueprint('startelection_api', __name__)

from time import sleep

import re
import os
import arrow       # date/time library
import random
import werkzeug

from flask_login import login_user, logout_user, current_user, login_required

from . import util
from . import database

@startelection_api.route("/s/<spacestring>/start-election", methods=["GET", "POST"])
def startelection(spacestring):

    START = 0
    CONFIRM_START_ELECTION = 1

    # TODO: Allow admin to set these values
    query = "Where would you like to have lunch at noon?"
    closeTime = "11:35"
    reminder = "A new election is at http://whereslunch.net/s/flaglunch"  # set up default reminder message to be sent to everyone

    if request.method == "GET":

        # show the confirmation page if the POST request from having just started an election redirected us here
        if "action" in request.args and int(request.args["action"]) == CONFIRM_START_ELECTION:
            date = None if ("date" not in request.args) else request.args["date"]
            params = {
                'action': CONFIRM_START_ELECTION,
                'reminder': reminder,
                'date': date,
                'query': query,
                'closeTime': closeTime,
                'urlForVotingSpace': url_for("votingspace_api.votingspace", spacestring=spacestring),

                'CONFIRM_START_ELECTION': 1
            }
        
            return render_template("startelection.html", **params)

        # we now know that we are rendering this page for the first time

        params = {
            'action': START,
            'reminder': reminder,
            'query': query,
            'closeTime': closeTime,
            'formAction': url_for("startelection_api.startelection", spacestring=spacestring),
            'urlForVotingSpace': url_for("votingspace_api.votingspace", spacestring=spacestring),
            
            'START': 0
        }

        return render_template("startelection.html", **params) # unpack the params dictionary, using its values as named parameters

    elif request.method == "POST":

        # make sure this is a reasonable hour to be texting people
        now = arrow.now()
        morning = now.replace(hour=8, minute=0, second=0)
        evening = now.replace(hour=19, minute=0, second=0)

        if now < morning:
            flash("Error: It is too early in the morning to set up an election", "error")
            return redirect(url_for('.startelection', spacestring=spacestring))
        if now > evening:
            flash("Error: It is too late in the day to set up an election", "error")
            return redirect(url_for('.startelection', spacestring=spacestring))

        # make sure the desired time voting closes isn't in the past
        voteEnd = now.replace(hour=int(closeTime.split(":")[0]), minute=int(closeTime.split(":")[1]), second=0)
        if (now >= voteEnd):
            flash("Error: Time voting closes cannot be in the past", "error")
            return redirect(url_for('.startelection', spacestring=spacestring))

        # make sure that there isn't already an election posted
        today = now.format("YYYY-MM-DD") # 4 digit year - 0 padded month - 0 padded day, psql's default format
        electionsToday = database.getElectionsOnDay(today, spacestring)
        if (len(electionsToday) != 0):
            flash("Error: There is already an election set up for today. You have been redirected to the page for that election.", "error")
            return redirect(url_for('votingspace_api.votingspace', spacestring=spacestring))

        # start a new election
        newElectionId = database.makeElection(today, query, closeTime, spacestring)
        print("Election started with ID: {}".format(newElectionId))

        # send out the messages reminding people to vote
        targetEmails = database.getReminderEmailAddresses(spacestring)
        for email in targetEmails:
            sleep(.1)
            util.sendEmail(email, reminder)
        
        params = {
            'action': CONFIRM_START_ELECTION,
            'reminder': reminder,
            'query': query,
            'closeTime': closeTime,
            'date': today,
            'spacestring': spacestring,
            
            'CONFIRM_START_ELECTION': 1
        }
        return redirect(url_for('.startelection', **params))

