#
# add-place
# A form for adding a new venue that can be selected in a ballot
#

from flask import render_template
from flask import url_for
from flask import request
from flask import session
from flask import Blueprint
from flask import flash
from flask import redirect
addplace_api = Blueprint('addplace_api', __name__)

import re
import os
import arrow       # date/time library
import random

from . import util
from . import database

@addplace_api.route("/s/<spacestring>/add-place", methods=["GET", "POST"])
def addplace(spacestring):

    # set up named constants that indicate what step we are currently on
    START = 0          # just display the user interface for submitting a venue
    JUST_ADDED = 1     # a new venue was just recorded in the database

    if request.method == "GET":
        
        # show the confirmation page if the POST request from having just added a new venue redirected us here
        if "action" in request.args and int(request.args["action"]) == JUST_ADDED:
            addedPlace = None if ("addedPlace" not in request.args) else request.args["addedPlace"]
        
            params = {
                'action': JUST_ADDED,
                'addedPlace': addedPlace,
                'urlForVotingSpace': url_for("votingspace_api.votingspace", spacestring=spacestring),

                'JUST_ADDED': 1
            }
        
            return render_template("addplace.html", **params)
        
        # we now know that we are rendering this page for the first time and must present the user with the input form
        
        closedVenues = [i[1] for i in database.getClosedVenues(spacestring)]
        params = {
            'action': START,
            'formAction': url_for("addplace_api.addplace", spacestring=spacestring),
            'venueList': database.getVenues(spacestring),
            'closedVenues': closedVenues,
            'addedPlace': "(none)",
            'urlForVotingSpace': url_for("votingspace_api.votingspace", spacestring=spacestring),

            'START': 0
        }
        return render_template("addplace.html", **params) # unpack the params dictionary, using its values as named parameters

    elif request.method == "POST":

        # figure out which action to perform based on what the POST data is
        addedPlace = "(none)"
        data = request.form
        if 'placeName' in data:
            addedPlace = data["placeName"]
            addedPlace = re.sub('[^a-z|A-Z|0-9|\-|\'|&|\s|\(|\)]', '', addedPlace)  # remove special characters from the new place name

            # make sure the place doesn't already exist
            venueObjectList = database.getVenues(spacestring)
            venueList = [o[1] for o in venueObjectList]
            if addedPlace in venueList:
                flash("Error: A place called \"{}\" already exists".format(addedPlace), "error")
                return redirect(url_for('.addplace', spacestring=spacestring))
                
            daysOpen = [
            "openDaysMo" in data,
            "openDaysTu" in data,
            "openDaysWe" in data,
            "openDaysTh" in data,
            "openDaysFr" in data,
            "openDaysSa" in data,
            "openDaysSu" in data]

            # add the new user-defined place to the database
            database.addVenue(addedPlace, daysOpen, spacestring)

        params = {
            'action': JUST_ADDED,
            'addedPlace': addedPlace,
            'spacestring': spacestring,

            'JUST_ADDED': 1
        }

        # don't render a template directly off of a POST request; redirect to a GET request, avoiding problems if the user manually reloads the page
        return redirect(url_for('.addplace', **params))
        
