#
# login
# The page for users to log in
#

from flask import render_template
from flask import url_for
from flask import session
from flask import request
from flask import Blueprint
from flask import flash
from flask import redirect
login_api = Blueprint('login_api', __name__)

from flask_login import login_user, logout_user, current_user, login_required

import os
import arrow       # date/time library
import random
import werkzeug

from . import util
from . import database

from flask_login import UserMixin

@login_api.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":

        next_ = '/' if ("next" not in request.args) else request.args.get("next")
        params = {
            'formAction': url_for("login_api.login"),
            'next': next_
        }

        return render_template("login.html", **params) # unpack the params dictionary, using its values as named parameters

    elif request.method == "POST":

        data = request.form
        password = str(data["password"])
        username = str(data["username"])
        next_ = str(data["next"])

        # find the hashed password associated with the given username
        passwordHash = database.getPasswordHash(username)

        # error if there is no such username, or the password is incorrect
        if passwordHash == -1 or not util.checkHash(passwordHash, password):
            flash("Invalid username or password", "error")
            return redirect(url_for(".login"))

        userId = database.getUserByName(username)['id']
        user = UserMixin()
        user.id = userId
        login_user(user)
        flash("Log in successful", "success")

        # don't render a template directly off of a POST request; redirect to a GET request, avoiding problems if the user manually reloads the page
        return redirect(next_)

