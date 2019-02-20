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
admin_api = Blueprint('admin_api', __name__)

from time import sleep

import os
import arrow       # date/time library
import random
import werkzeug

from flask_login import login_user, logout_user, current_user, login_required

from . import util
from . import database

@admin_api.route("/s/<spacestring>/admin", methods=["GET", "POST"])
@login_required
def admin(spacestring):

    now = arrow.now()

    # set up named constants that indicate what action is being performed
    START = 0
    CONFIRM_ADD_ELECTION = 1
    CONFIRM_ADD_MESSAGE = 2
    CONFIRM_SEND_REMINDERS = 3
    CONFIRM_EDIT_ELECTION = 4
    CONFIRM_DROP_ELECTION = 5

    if request.method == "GET":

        urlForLogout = url_for("logout_api.logout", spacestring=spacestring)

        # show the confirmation page if the POST request from having just performed an action redirected us here
        if "action" in request.args and int(request.args["action"]) != START:

            # convert all incoming parameters from Unicode to ASCII so that they aren't displayed like this: [u'42']
            params = {
                'urlForLogout': urlForLogout,
                'urlForAdmin': url_for("admin_api.admin", spacestring=spacestring)
            }
            for key, value in request.args.items():
                if key == 'targetEmails':
                    params[key] = request.args.getlist(key) # this is a list, so it should not simply be cast to a string
                else:
                    params[key] = str(value)

            ### urlForStartElection=url_for("startelection_api.startelection", spacestring=spacestring),
            return render_template("admin.html", **params)

        # we now know that we are rendering this page for the first time and must present the user with options
        query = "Where would you like to have lunch at 12:45?"
        today = now.format("YYYY-MM-DD") # 4 digit year - 0 padded month - 0 padded day, psql's default format
        time = "12:10"

        params = {
            'action': START,
            'query': query,
            'date': today,
            'time': time,
            'formAction': url_for("admin_api.admin", spacestring=spacestring),
            'urlForAdmin': url_for("admin_api.admin", spacestring=spacestring),
            'urlForLogout': urlForLogout,

            'START': 0
        }

        return render_template("admin.html", **params) # unpack the params dictionary, using its values as named parameters

    elif request.method == "POST":

        data = request.form

        # determine the action based on the function type
        functionType = str(data["function-type"])

        if functionType == "new-election":

            query = str(data["query"]).strip()
            date = str(data["date"]).strip()
            time = str(data["time"]).strip()

            if len(query) == 0:
                flash("Error: Query string is empty", "error")
                return redirect(url_for("admin_api.admin", spacestring=spacestring))

            # TODO: Make sure date is not in the past (startelection.py might have code to copy)
            # TODO: Make sure there's not already an election running

            newElectionId = database.makeElection(date, query, time, spacestring)

            params = {
                'action': CONFIRM_ADD_ELECTION,
                'functionType': functionType,
                'query': query,
                'date': date,
                'time': time,
                'electionId': newElectionId,
                'spacestring': spacestring,

                'CONFIRM_ADD_ELECTION': 1
            }
            return redirect(url_for('.admin', **params))

        elif functionType == "new-message":

            tmpMessage = str(data["temp-message"]).strip()
            messageExp = str(data["message-exp"]).strip()

            # TODO: Add sanity checking
            database.makeMessage(tmpMessage, messageExp)

            params = {
                'action': CONFIRM_ADD_MESSAGE,
                'functionType': functionType,
                'tmpMessage': tmpMessage,
                'messageExp': messageExp,
                'spacestring': spacestring,

                'CONFIRM_ADD_MESSAGE': 2
            }
            return redirect(url_for('.admin', **params))

        elif functionType == "send-reminders":

            reminderText = str(data["reminder-text"]).strip()

            targetEmails = database.getReminderEmailAddresses(spacestring)
            for email in targetEmails:
                sleep(.1)
                util.sendEmail(email, reminderText)

            params = {
                'action': CONFIRM_SEND_REMINDERS,
                'functionType': functionType,
                'reminderText': reminderText,
                'targetEmails': targetEmails,
                'spacestring': spacestring,

                'CONFIRM_SEND_REMINDERS': 3
            }
            return redirect(url_for('.admin', **params))

        elif functionType == "edit-election":

            newTime = str(data["new-time"])

            database.changeTime(newTime, spacestring)

            params = {
                'action': CONFIRM_EDIT_ELECTION,
                'functionType': functionType,
                'newTime': newTime,
                'spacestring': spacestring,

                'CONFIRM_EDIT_ELECTION': 4
            }
            return redirect(url_for('.admin', **params))

        elif functionType == "drop-election":

            database.dropTodaysElection(spacestring)

            params = {
                'action': CONFIRM_DROP_ELECTION,
                'functionType': functionType,
                'spacestring': spacestring,

                'CONFIRM_DROP_ELECTION': 5
            }
            return redirect(url_for('.admin', **params))

        else:

            flash("Error: Unrecognized function type: {}".format(functionType), "error")
            return redirect(url_for("admin_api.admin", spacestring=spacestring))
