#
# register
# The page for new users to register
#

from flask import render_template
from flask import url_for
from flask import session
from flask import request
from flask import Blueprint
from flask import flash
from flask import redirect
register_api = Blueprint('register_api', __name__)

from time import sleep

import os
import arrow       # date/time library
import random
import werkzeug

from . import util
from . import database

@register_api.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":

        # set up named constants that indicate what action is being performed
        NONE = 0

        # by default, only display the user interface
        action = NONE

        formAction = url_for("register_api.register")

        params = {
            'title': 'page title',
            'action': action,
            'formAction': formAction,
            
            'NONE': 0,
        }

        return render_template("register.html", **params) # unpack the params dictionary, using its values as named parameters

    # process a POST request
    NONE = 0
    data = request.form
    password = str(data["password"])
    username = str(data["username"])

    # determine the action
    action = NONE

    database.registerNewUser(username, password)
    flash("New user created: {}".format(username), "success")

    params = {
        'title': 'page title',
        'action': action,
        'username': username,
        
        'NONE': 0,
    }

    return render_template("register.html", **params) # unpack the params dictionary, using its values as named parameters

