#
# feedback
# A form for giving general feedback about the app, such as reporting a bug or suggesting a feature
#

from flask import render_template
from flask import url_for
from flask import request
from flask import session
from flask import flash
from flask import redirect
from flask import Blueprint
feedback_api = Blueprint('feedback_api', __name__)

import re
import os
import arrow       # date/time library
import random

from . import util
from . import database

@feedback_api.route("/feedback", methods=["GET", "POST"])
def feedback():

    # set up named constants that indicate what action is being performed
    START = 0
    THANK_USER = 1

    if request.method == "GET":

        # show the confirmation page, thanking the user for their feedback
        if "action" in request.args and int(request.args["action"]) == THANK_USER:
            params = {
                'action': THANK_USER,
                'THANK_USER': 1
            }

            return render_template("feedback.html", **params)

        # we now know that we are rendering this page for the first time and must present the user with the input form

        params = {
            'action': START,
            'formAction': url_for("feedback_api.feedback"),
            'START': 0
        }
        return render_template("feedback.html", **params) # unpack the params dictionary, using its values as named parameters

    elif request.method == "POST":
        data = request.form

        action = THANK_USER

        feedbackType = str(data["type"])
        feedbackText = str(data["text"])

        feedbackTarget = ""
        if "FEEDBACK_TARGET" in os.environ:
            feedbackTarget = os.environ["FEEDBACK_TARGET"]

        now = arrow.now().format("YYYY-MM-DD HH:mm:ss")

        # print feedback to std out if no target email to send it to is specified
        if feedbackTarget == "":
            print("User feedback ({})".format(now))
            print("    type:  {}".format(feedbackType))
            print("    text:  {}".format(feedbackText))
        else:
            util.sendEmail(feedbackTarget, "User feedback on date: {}\ntype:{}\ntext:{}".format(now, feedbackType, feedbackText))

        params = {
            'action': action,
            'feedbackType': feedbackType,
            'feedbackText': feedbackText,

            'THANK_USER': 1
        }

        # don't render a template directly off of a POST request; redirect to a GET request, avoiding problems if the user manually reloads the page
        return redirect(url_for('.feedback', **params))
