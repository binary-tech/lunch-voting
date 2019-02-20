#
# util.php
# Provides miscellaneous helpful functions.
#

import os
import arrow
import string
import psycopg2
import smtplib
from html.parser import HTMLParser
import werkzeug
from urllib import parse

# credit: http://stackoverflow.com/questions/753052/strip-html-from-strings-in-python
class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

# strip HTML special characters instead of encoding them
# credit: http://stackoverflow.com/questions/753052/strip-html-from-strings-in-python
def sanitizeInput(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def makeConn():
    user = None
    password = None
    host = None
    port = None
    database = None
    if "DATABASE_URL" in os.environ:
        user, password, host, port, database = parseDbUrl(os.environ["DATABASE_URL"])
    else:
        user = os.environ["PGUSER"]
        password = os.environ["PGPASSWORD"]
        host = os.environ["PGHOST"]
        port = 5432
        database = os.environ["PGDATABASE"]

    return psycopg2.connect(user=user, password=password, host=host, port=port, database=database)

def parseDbUrl(url):
    o = parse.urlparse(url)
    return o.username, o.password, o.hostname, o.port, o.path[1:]

#
# Send an email
#
def sendEmail(address, content):
    print("Sending email over SMTP to {}".format(address))

    from email.mime.text import MIMEText

    msg = MIMEText(content)
    msg["Subject"] = "Lunch"
    msg["From"]    = "noreply@mg.whereslunch.net"
    msg["To"]      = address

    s = smtplib.SMTP("smtp.mailgun.org", 587)

    try:
        s.login("postmaster@mg.whereslunch.net", os.environ["MG_SMTP_PASS"])
        s.sendmail(msg["From"], msg["To"], msg.as_string())
        s.quit()
    except smtplib.SMTPException as e:
        print("SMTPException:", e)

#
# If necessary, trim a string to conform to a given max length
#
def trimToMaxLength(s, maxLength):
    if len(s) > maxLength:
        return s[:maxLength]
    else:
        return s

# rot18 encode a string (A becomes S, B becomes T, etc.)
# Only alpha-numeric characters are allowed, and all characters come out uppercase
def rot18(s):
    alphaNumeric = string.ascii_uppercase + string.digits
    return ''.join([alphaNumeric[(alphaNumeric.index(c) + 18 ) % 36] for c in s.upper()])

# rot18 encode a series of comma-separated strings
def rot18csv(s):
    return ','.join([rot18(i) for i in s.split(",")])

#
# Make a hash of any string, strong enough for storing passwords
#
def makeHash(s):
    return werkzeug.generate_password_hash(s)

#
# Check a hash, used for checking that a password is correct
#
def checkHash(h, s):
    return werkzeug.check_password_hash(h, s)

#
# Return two-character code that represents the current day, such as 'su' or 'mo'
#
def getTodayCode():
    return str(arrow.now().format("ddd")[:2].lower())

#
# Turn the DictCursor result from the database into real dictionaries
#
def toDicts(iterable):
    result = []
    for i in iterable:
        result.append(dict(i))
    return result

