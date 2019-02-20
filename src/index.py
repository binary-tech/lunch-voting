#
# index
# The first page viewed by the user
#

from flask import render_template
from flask import url_for
from flask import session
from flask import request
from flask import Blueprint
from flask import flash
from flask import redirect
index_api = Blueprint('index_api', __name__)

import os
import arrow       # date/time library
import random

import re
from . import util
from . import database

from flask import current_app

@index_api.route("/", methods=["GET", "POST"])
def index():

    params = {
        'urlForFeedback': url_for("feedback_api.feedback")
    }
    return render_template("index.html", **params) # unpack the params dictionary, using its values as named parameters

