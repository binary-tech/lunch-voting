#
# database
# Provides functions for interacting with the database
#

from flask import g

import re
import psycopg2
import psycopg2.extras
from operator import itemgetter
import string
import random

import arrow

from . import util

# define limits to how large the database can become
MAX_STRING_LENGTH = 100

#
# Take an id and the name of a table, which can be either people or venues,
# and return the name of the person or venue
#
def getNameById(id_, tableName, vsPublicId):
    votingSpaceId = getVotingSpaceId(vsPublicId)

    if (id_ == None):
        return '(no preference)'
    id_ = int(id_)
    if (id_ == -1):
        return '(no preference)'
    query = 'SELECT name FROM ' + str(tableName) + ' WHERE id=%s AND votingspace=%s'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(query, [id_, votingSpaceId])
    queryResult = cursor.fetchone()
    cursor.close()
    if queryResult == None:
        return None

    return str(queryResult[0])

#
# Convenience function that returns all visible venues as an array of dictionaries
# with properties such as 'id' and 'name'
#
def getVenues(vsPublicId):
    votingSpaceId = getVotingSpaceId(vsPublicId)

    query = 'SELECT * FROM venues WHERE visible=TRUE AND votingspace=%s ORDER BY lower(name)'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(query, [int(votingSpaceId)])
    queryResult = cursor.fetchall()
    cursor.close()
    
    allRows = queryResult

    # change 'The Place' to 'Place, The'
    result = []
    for row in allRows:
        name = row['name']
        if name.lower().startswith("the "):
            name = name[4:] + ", " + name[:3]
        elif name.lower().startswith("a "):
            name = name[2:] + ", " + name[:1]
        elif name.lower().startswith("an "):
            name = name[3:] + ", " + name[:2]

        result.append([row['id'], name])

    # re-alphabetize, now that correction have been made
    return sorted(result, key=itemgetter(1))

#
# Convenience function that returns all visible venues that are open today as an array of dictionaries
# with properties such as 'id' and 'name'
#
def getOpenVenues(vsPublicId):
    votingSpaceId = getVotingSpaceId(vsPublicId)
    todayCode = util.getTodayCode()  # code for current day of the week ('su', 'mo', etc)

    query = 'SELECT * FROM venues LEFT OUTER JOIN (SELECT venues.id, days_closed.venueid FROM venues INNER JOIN days_closed ON venues.id = days_closed.venueid WHERE day=%s) AS closed_that_day USING (id) WHERE closed_that_day.venueid IS NULL AND venues.visible=true AND venues.votingspace=%s ORDER BY lower(venues.name)'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(query, [str(todayCode), int(votingSpaceId)])
    queryResult = cursor.fetchall()
    colnames = [desc[0] for desc in cursor.description]
    cursor.close()
    
    allRows = queryResult

    # change 'The Place' to 'Place, The'
    result = []
    for row in allRows:
        name = row['name']
        if name.lower().startswith("the "):
            name = name[4:] + ", " + name[:3]
        elif name.lower().startswith("a "):
            name = name[2:] + ", " + name[:1]
        elif name.lower().startswith("an "):
            name = name[3:] + ", " + name[:2]

        result.append([row['id'], name])

    # re-alphabetize, now that correction have been made
    return sorted(result, key=itemgetter(1))

#
# Convenience function that returns all visible venues that are closed today as an array of dictionaries
# with properties such as 'id' and 'name'
#
def getClosedVenues(vsPublicId):
    votingSpaceId = getVotingSpaceId(vsPublicId)
    todayCode = util.getTodayCode()  # code for current day of the week ('su', 'mo', etc)

    query = 'SELECT * FROM venues INNER JOIN days_closed ON venues.id = days_closed.venueid WHERE day=%s AND venues.visible=true AND venues.votingspace=%s ORDER BY lower(venues.name)'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(query, [str(todayCode), int(votingSpaceId)])
    queryResult = cursor.fetchall()
    cursor.close()
    
    allRows = queryResult

    # change 'The Place' to 'Place, The'
    result = []
    for row in allRows:
        name = row['name']
        if name.lower().startswith("the "):
            name = name[4:] + ", " + name[:3]
        elif name.lower().startswith("a "):
            name = name[2:] + ", " + name[:1]
        elif name.lower().startswith("an "):
            name = name[3:] + ", " + name[:2]

        result.append([row['id'], name])

    # re-alphabetize, now that correction have been made
    return sorted(result, key=itemgetter(1))

#
# Pull everyone's votes out of the database for a particular election
#
def getVotes(electionId):
    query = "SELECT * FROM votes WHERE electionId=%s ORDER BY changed"
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(query, [int(electionId)])
    queryResult = cursor.fetchall()
    cursor.close()
    return queryResult

#
# Pull preferences associated with a vote, returning them as a list starting with first preference
#
def getPrefs(voteId):
    query = "SELECT venueid FROM vote_prefs WHERE voteid=%s ORDER BY rank ASC"
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(query, [int(voteId)])
    queryResult = cursor.fetchall()
    cursor.close()
    return queryResult

#
# Get a list of unique venue id's that were voted for at least once for a particular election, with no duplicates
# Used for indicating which venues have been voted for when the user is constructing their vote
#
def getUniqueVotes(electionId):
    query = "SELECT DISTINCT vote_prefs.venueid FROM votes INNER JOIN vote_prefs ON votes.id=vote_prefs.voteid WHERE vote_prefs.venueid IS NOT NULL AND votes.electionid=%s"
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(query, [int(electionId)])
    queryResult = cursor.fetchall()
    cursor.close()

    # TODO: There has to be a more elegant way to solve this issue
    return [i[0] for i in queryResult]

#
# Return the elections for a given day, with the day being of the format Y-m-d (psql's default date format)
#
def getElectionsOnDay(day, vsPublicId):
    votingSpaceId = getVotingSpaceId(vsPublicId)
    if votingSpaceId == None:
        return None

    query = 'SELECT * FROM elections WHERE dayOfElection=%s AND votingspace=%s'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(query, [str(day), int(votingSpaceId)])
    queryResult = cursor.fetchall()
    cursor.close()
    return queryResult

#
# Return the id of the voting space based on its public id or None if there is no such voting space
#
def getVotingSpaceId(publicId):
    query = 'SELECT id FROM voting_spaces WHERE publicid=%s'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(query, [str(publicId)])
    queryResult = cursor.fetchone()
    cursor.close()
    if queryResult == None:
        return None
    else:
        return queryResult[0]

#
# Return all the one-off messages that have not yet expired
#
def getOneOffMessages():
    query = 'SELECT * FROM messages WHERE expires > CURRENT_DATE'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(query)
    queryResult = cursor.fetchall()
    cursor.close()
    return queryResult

#
# Get all emails to send messages to when a new election reminder must go out
#
def getReminderEmailAddresses(vsPublicId):
    votingSpaceId = getVotingSpaceId(vsPublicId)

    query = 'SELECT email FROM contacts WHERE tellaboutposts=TRUE AND votingspace=%s'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(query, [int(votingSpaceId)])
    queryResult = cursor.fetchall()
    cursor.close()

    emailAddresses = []
    for contact in queryResult:
        if contact["email"] != None:
            emailAddresses.append(contact["email"])
    return emailAddresses

#
# Get all emails to send messages to when results for an election have been counted
#
def getResultsEmailAddresses(vsPublicId):
    votingSpaceId = getVotingSpaceId(vsPublicId)

    query = 'SELECT email FROM contacts WHERE tellaboutresults=TRUE AND votingspace=%s'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(query, [int(votingSpaceId)])
    queryResult = cursor.fetchall()
    cursor.close()

    emailAddresses = []
    for contact in queryResult:
        if contact["email"] != None:
            emailAddresses.append(contact["email"])
    return emailAddresses

#
# Enter a new venue into the database (done via add-place.php)
# daysOpen is a length 7 list of binary values, true if open that day, first entry specifies Monday
#
def addVenue(venueName, daysOpen, vsPublicId):
    votingSpaceId = getVotingSpaceId(vsPublicId)

    # record the new venue itself
    venueName = util.trimToMaxLength(venueName, MAX_STRING_LENGTH)
    stmt = 'INSERT INTO venues (name, votingspace) VALUES (%s, %s) RETURNING id'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(stmt, [str(venueName), int(votingSpaceId)])
    venueId = cursor.fetchone()[0]

    # record the days this new venue is closed
    stmt = 'INSERT INTO days_closed VALUES (%s, %s)'
    dayCodes = ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su']
    for i, isOpen in enumerate(daysOpen):
        if not isOpen:
            cursor.execute(stmt, [int(venueId), str(dayCodes[i])])

    g.conn.commit()
    cursor.close()

#
# Find the winning venue id for a particular election id
#
def getWinnerForElection(electionId):
    query = 'SELECT winner FROM elections WHERE id=%s'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(query, [str(electionId)])
    queryResult = cursor.fetchone()
    cursor.close()
    return queryResult[0]

#
# Find the contact that corresponds to the given email address
# Used to avoid adding duplicate contacts
#
def getContactByEmail(email, vsPublicId):
    votingSpaceId = getVotingSpaceId(vsPublicId)

    query = 'SELECT * FROM contacts WHERE email=%s AND votingspace=%s'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(query, [str(email), int(votingSpaceId)])
    queryResult = cursor.fetchone()
    cursor.close()
    if queryResult == None:
        return None
    else:
        return queryResult

#
# Change the notification settings for a contact, such as if they want to be notified when a new election is posted
#
def updateContactNotifications(email, tellAboutPosts, tellAboutResults, vsPublicId):
    votingSpaceId = getVotingSpaceId(vsPublicId)

    stmt = 'UPDATE contacts SET tellaboutposts=%s, tellaboutresults=%s WHERE email=%s AND votingspace=%s'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(stmt, [tellAboutPosts, tellAboutResults, email, votingSpaceId])
    g.conn.commit()
    cursor.close()

#
# Enter a new vote into the database and return the new vote's id
# prefs is expected to be a tuple of ranked preferences, usually 3, starting with most preferred
#
def recordVote(electionId, prefs):
    stmt = 'INSERT INTO votes (electionId) VALUES (%s) RETURNING id'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(stmt, [int(electionId)])
    voteId = int(cursor.fetchone()[0])

    for i, pref in enumerate(prefs):
        stmt = 'INSERT INTO vote_prefs (voteid, venueid, rank) VALUES (%s, %s, %s)'
        cursor.execute(stmt, [voteId, pref, i + 1])

    g.conn.commit()
    cursor.close()

    return voteId

#
# Edit an existing vote
# prefs is expected to be a tuple of ranked preferences, usually 3, starting with most preferred
#
def updateVote(voteId, prefs):
    stmt = 'UPDATE votes SET changed=now() WHERE id=%s'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(stmt, [int(voteId)])

    # remove existing prefs for this vote so that new ones can be added
    stmt = 'DELETE FROM vote_prefs WHERE voteid=%s'
    cursor.execute(stmt, [int(voteId)])

    # add the new prefs
    for i, pref in enumerate(prefs):
        stmt = 'INSERT INTO vote_prefs (voteid, venueid, rank) VALUES (%s, %s, %s)'
        cursor.execute(stmt, [voteId, pref, i + 1])

    g.conn.commit()
    cursor.close()

#
# Enter the winning venue for a particular election
#
def recordWinner(electionId, winningVenueId):
    # TODO: Throw an error if winningVenueId type is not an int or None
    stmt = 'UPDATE elections SET winner=%s WHERE id=%s'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(stmt, [winningVenueId, int(electionId)])
    g.conn.commit()
    cursor.close()

#
# Generate a small key that can be used to edit a vote, and make sure that it is unique
# TODO: Limit total votes so that it is guaranteed to always be able to generate a unique key
#
def generateKey():
    profaneRegex = re.compile(util.rot18csv("SAA,SNN,SAN,SNA,XC2,U5B,AWF,ALF,AZB,A0B,AJB,UCB,UCP,2CB,7AA,70A,7JA,BS5,S55,TS5,B0B,BJB,302,3J2,XCU,222,5H0"))

    result = ''
    while len(result) == 0 or profaneRegex.match(result) or getVoteForKey(result) != -1:
        result = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return result

#
# Find the vote id for a key, or -1 if the key does not yet exist
#
def getVoteForKey(key):
    # TODO: return None instead of -1
    query = 'SELECT id FROM votes WHERE key=%s'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(query, [str(key)])
    queryResult = cursor.fetchone()
    cursor.close()
    if queryResult == None:
        return -1
    else:
        return queryResult[0]

#
# Return true if the specified key corresponds to an election that has ended
# TODO: restrict down to the minute, not just the day
#
def voteKeyHasExpired(key):
    query = 'SELECT * FROM elections INNER JOIN votes ON votes.electionid=elections.id WHERE votes.key=%s AND elections.dayofelection >= date(now());'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(query, [str(key)])
    queryResult = cursor.fetchone()
    cursor.close()
    if queryResult == None:
        return True
    else:
        return False

#
# Assign a specified unique key to a vote, so that it can be edited
#
def setVoteKey(voteId, voteKey):
    stmt = 'UPDATE votes SET key=%s WHERE id=%s'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(stmt, [str(voteKey), int(voteId)])
    g.conn.commit()
    cursor.close()

#
# Return the password hash stored in the database for a user
#
def getPasswordHash(username):
    query = 'SELECT password FROM users WHERE username=%s'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(query, [str(username)])
    queryResult = cursor.fetchone()
    cursor.close()
    if queryResult == None:
        return -1
    else:
        return queryResult[0]

#
# Add a new election to the database and return its id
#
def makeElection(dayofelection, query, timevotingends, vsPublicId):

    # TODO implement closing timestamps
    # make an Arrow-based representation of the start and end timestamps
    # print "NEW ELECTION: {}".format("{} {}".format(dayofelection, timevotingends))
    # closingTimestamp = arrow.get("{} {}".format(dayofelection, timevotingends), "YYYY-MM-DD HH:mm")

    votingSpaceId = getVotingSpaceId(vsPublicId)

    stmt = 'INSERT INTO elections (dayofelection, query, timevotingends, votingspace) VALUES (date(%s), %s, %s, %s) RETURNING id'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(stmt, [dayofelection, query, timevotingends, votingSpaceId])
    electionId = cursor.fetchone()
    g.conn.commit()
    cursor.close()
    return int(electionId[0])

#
# Add a new message to the database and return its id
#
def makeMessage(message, expiration):
    stmt = 'INSERT INTO messages (expires, content) VALUES (now()+interval %s, %s) RETURNING id'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(stmt, [expiration, message])
    messageId = cursor.fetchone()
    g.conn.commit()
    cursor.close()
    return int(messageId[0])

#
# Add a new contact email to the list, for notifying when a new election is available, and return its id
#
def addEmail(newEmail, tellAboutPosts, tellAboutResults, vsPublicId):
    votingSpaceId = getVotingSpaceId(vsPublicId)

    stmt = 'INSERT INTO contacts (tellaboutposts, tellaboutresults, email, votingspace) VALUES (%s, %s, %s, %s) RETURNING id'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(stmt, [tellAboutPosts, tellAboutResults, newEmail, votingSpaceId])
    contactId = cursor.fetchone()
    g.conn.commit()
    cursor.close()
    return int(contactId[0])

#
# Delete a mass contact email address, because a user doesn't want to be notified about elections anymore
#
def deleteEmail(email, vsPublicId):
    votingSpaceId = getVotingSpaceId(vsPublicId)

    stmt = 'DELETE FROM contacts WHERE email=%s AND votingspace=%s'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(stmt, [email, votingSpaceId])
    g.conn.commit()
    cursor.close()

#
# Register a new user into the system, and return the new id number
#
def registerNewUser(username, password):
    passwordHash = util.makeHash(password)
    stmt = 'INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(stmt, [username, passwordHash])
    userId = cursor.fetchone()
    g.conn.commit()
    cursor.close()
    return int(userId[0])

#
# Get the user for a specified id
#
def getUser(idNumber):
    query = 'SELECT * FROM users WHERE id=%s'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(query, [idNumber])
    queryResult = cursor.fetchone()
    cursor.close()
    if queryResult == None:
        return None

    return queryResult

#
# Get the user for a specified name
#
def getUserByName(name):
    query = 'SELECT * FROM users WHERE username=%s'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(query, [name])
    queryResult = cursor.fetchone()
    cursor.close()
    if queryResult == None:
        return None

    return queryResult

#
# Change the end time for the current election
# vsPublicId means voting space public id
#
def changeTime(newTime, vsPublicId):
    now = arrow.now()
    today = now.format("YYYY-MM-DD") # 4 digit year - 0 padded month - 0 padded day, psql's default format
    
    electionsToday = getElectionsOnDay(today, vsPublicId)
    if len(electionsToday) == 0:
        raise Exception("no elections today")
    todaysElection = electionsToday[0]

    stmt = 'UPDATE elections SET timevotingends=%s WHERE id=%s'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(stmt, [newTime, int(todaysElection['id'])])
    g.conn.commit()
    cursor.close()

#
# Delete today's election
# vsPublicId means voting space public id
#
def dropTodaysElection(vsPublicId):
    now = arrow.now()
    today = now.format("YYYY-MM-DD") # 4 digit year - 0 padded month - 0 padded day, psql's default format
    
    electionsToday = getElectionsOnDay(today, vsPublicId)
    if len(electionsToday) == 0:
        raise Exception("no elections today")
    todaysElection = electionsToday[0]

    stmt = 'DELETE FROM elections WHERE id=%s'
    cursor = g.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(stmt, [int(todaysElection['id'])])
    g.conn.commit()
    cursor.close()

