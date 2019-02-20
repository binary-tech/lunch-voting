#
# listplaces.py
# List out the venues available when an election is running
#

from flask import render_template
from flask import url_for
from flask import session
from flask import request
from flask import Blueprint
from flask import flash
from flask import redirect
listplaces_api = Blueprint('listplaces_api', __name__)

import os
import arrow       # date/time library
import random

import re
from . import util
from . import database

from flask import current_app

@listplaces_api.route("/s/<spacestring>/list-places", methods=["GET", "POST"])
def listplaces(spacestring):

    params = {
        'venueList': database.getVenues(spacestring),
        'urlForVotingSpace': url_for("votingspace_api.votingspace", spacestring=spacestring)
    }
    return render_template("listplaces.html", **params) # unpack the params dictionary, using its values as named parameters

