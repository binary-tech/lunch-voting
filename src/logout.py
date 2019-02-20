#
# logout
# The page for users to log out
#

from flask import render_template
from flask import url_for
from flask import session
from flask import request
from flask import Blueprint
from flask import flash
from flask import redirect
logout_api = Blueprint('logout_api', __name__)

from flask_login import login_user, logout_user, current_user, login_required

@logout_api.route("/s/<spacestring>/logout", methods=["GET", "POST"])
@login_required
def logout(spacestring):
    logout_user()
    flash("Logged out", "success")
    return redirect(url_for("votingspace_api.votingspace", spacestring=spacestring))

