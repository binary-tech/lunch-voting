import os

from flask import Flask
app = Flask(__name__)

from flask import g

from flask_login import LoginManager
from flask_login import UserMixin
import src.util as util
import src.database as database

from src.index import index_api
from src.addplace import addplace_api
from src.admin import admin_api
from src.register import register_api
from src.login import login_api
from src.logout import logout_api
from src.addcontact import addcontact_api
from src.startelection import startelection_api
from src.votingspace import votingspace_api
from src.listplaces import listplaces_api
from src.feedback import feedback_api

# put the app in debug mode if the environment variable DEBUG is 1
app.debug = False
if "DEBUG" in os.environ:
    if os.environ["DEBUG"] == "1":
        print("=== Debug mode active ===")
        app.debug = True

app.secret_key = '\xf6"L\x1f\x84>?V\xfej\xdf~\xc9u\xde\xffa\xc7k\xc7\xe6\x16\x11U'

app.register_blueprint(index_api)
app.register_blueprint(addplace_api)
app.register_blueprint(admin_api)
app.register_blueprint(register_api)
app.register_blueprint(login_api)
app.register_blueprint(logout_api)
app.register_blueprint(addcontact_api)
app.register_blueprint(startelection_api)
app.register_blueprint(votingspace_api)
app.register_blueprint(listplaces_api)
app.register_blueprint(feedback_api)

lm = LoginManager()

@lm.user_loader
def load_user(username):
    userId = database.getUser(username)['id']
    user = UserMixin()
    user.id = userId
    return user

lm.init_app(app)
lm.login_view = '/login'

# set up a database connection before each request
@app.before_request
def before_request():
    g.version = "beta 8"
    g.minVoteCount = 4     # minimum number of votes required for an election to count as legit
    g.conn = util.makeConn()

# discourage browser caching
@app.after_request
def apply_caching(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
    response.headers["Pragma"] = "no-cache" # HTTP 1.0.
    response.headers["Expires"] = "0" # Proxies.
    return response

# close the database connection after each request, even if an exception occurred
@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'conn', None)
    if db is not None:
        db.close()

if __name__ == "__main__":
    if "PORT" in os.environ:
        app.run(port=int(os.environ["PORT"]))
    else:
        app.run()
