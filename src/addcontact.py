#
# add-contact
# A form for adding a new user email to contact automatically about election results, or remove an email from the list
#

from flask import render_template
from flask import url_for
from flask import request
from flask import session
from flask import flash
from flask import redirect
from flask import Blueprint
addcontact_api = Blueprint('addcontact_api', __name__)

import re
import os
import arrow       # date/time library
import random

from . import util
from . import database

@addcontact_api.route("/s/<spacestring>/add-contact", methods=["GET", "POST"])
def addcontact(spacestring):

    # set up named constants that indicate what action is being performed
    START = 0
    ADD_CONTACT = 1
    RM_CONTACT = 2

    if request.method == "GET":

        # show the confirmation page if the POST request from having just added a new contact redirected us here
        if "action" in request.args and int(request.args["action"]) == ADD_CONTACT:
            addedEmail = None if ("addedEmail" not in request.args) else request.args["addedEmail"]
            tellAboutPosts = None if ("tellAboutPosts" not in request.args) else request.args["tellAboutPosts"]
            tellAboutResults = None if ("tellAboutResults" not in request.args) else request.args["tellAboutResults"]

            params = {
                'action': ADD_CONTACT,
                'addedEmail': addedEmail,
                'tellAboutPosts': tellAboutPosts,
                'tellAboutResults': tellAboutResults,
                'urlForVotingSpace': url_for("votingspace_api.votingspace", spacestring=spacestring),
                'ADD_CONTACT': 1
            }
        
            return render_template("addcontact.html", **params)

        # show the confirmation page if the POST request was for removing a contact
        if "action" in request.args and int(request.args["action"]) == RM_CONTACT:
            rmedEmail = None if ("rmedEmail" not in request.args) else request.args["rmedEmail"]

            params = {
                'action': RM_CONTACT,
                'rmedEmail': rmedEmail,
                'urlForVotingSpace': url_for("votingspace_api.votingspace", spacestring=spacestring),
                'RM_CONTACT': 2
            }
        
            return render_template("addcontact.html", **params)
        
        # we now know that we are rendering this page for the first time and must present the user with the input form

        params = {
            'action': START,
            'formAction': url_for("addcontact_api.addcontact", spacestring=spacestring),
            'urlForVotingSpace': url_for("votingspace_api.votingspace", spacestring=spacestring),
            'START': 0
        }
        return render_template("addcontact.html", **params) # unpack the params dictionary, using its values as named parameters

    elif request.method == "POST":
        data = request.form

        action = START

        addedEmail = "(none)"
        rmedEmail = "(none)"
        tellAboutPosts = True
        tellAboutResults = True

        if data['addedEmail'].strip() == "" and data['rmedEmail'].strip() == "":
            flash("Error: Form not complete", "error")
            return redirect(url_for('.addcontact', spacestring=spacestring))

        if data['addedEmail'].strip() != "":
            action = ADD_CONTACT
            tellAboutPosts = "tellAboutPosts" in data     # send a text when a new election is available
            tellAboutResults = "tellAboutResults" in data # send a text with the results of an election
            addedEmail = str(data["addedEmail"]).lower()

            # check for an existing number that matches, to avoid duplicates
            duplicateEmail = database.getContactByEmail(addedEmail, spacestring)
            if duplicateEmail == None:
                database.addEmail(addedEmail, tellAboutPosts, tellAboutResults, spacestring)
                flash("Email address {} added successfully".format(addedEmail), "success")
            else:
                # if this email already exits but with different notification settings, update the notification settings instead of flashing an error
                if duplicateEmail["tellaboutposts"] != tellAboutPosts or duplicateEmail["tellaboutresults"] != tellAboutResults:
                    database.updateContactNotifications(addedEmail, tellAboutPosts, tellAboutResults, spacestring)
                    flash("Updated notification settings for email address {}".format(addedEmail), "success")
                else:
                    flash("Error: The email address {} already exists".format(addedEmail), "error")
                return redirect(url_for('.addcontact', spacestring=spacestring))

        if data['rmedEmail'].strip() != "":
            action = RM_CONTACT
            rmedEmail = str(data["rmedEmail"]).lower()

            # check to make sure the email exists before deleting it
            existingEmail = database.getContactByEmail(rmedEmail, spacestring)
            if existingEmail == None:
                flash("Error: The email address {} does not exist".format(rmedEmail), "error")
                return redirect(url_for('.addcontact', spacestring=spacestring))
            else:
                database.deleteEmail(rmedEmail, spacestring)
                flash("Email address {} deleted successfully".format(rmedEmail), "success")

        params = {
            'action': action,
            'addedEmail': addedEmail,
            'rmedEmail': rmedEmail,
            'tellAboutPosts': tellAboutPosts,
            'tellAboutResults': tellAboutResults,
            'spacestring': spacestring,

            'ADD_CONTACT': 1,
            'RM_CONTACT': 2
        }

        # don't render a template directly off of a POST request; redirect to a GET request, avoiding problems if the user manually reloads the page
        return redirect(url_for('.addcontact', **params))

