Overview
========

This project is a web app designed to allow groups of people to cast votes to decide where to go for lunch. These votes are then tallied and a winner is revealed, enhancing coordination and reducing the need for mass texting.

Developing on a Local Computer
==============================

## All Instructions Assume This Software is Installed
    * [git 2.10](https://git-scm.com)
    * [heroku cli 5.7](https://devcenter.heroku.com/articles/heroku-cli)
    * [python 3.6](https://www.python.org)

## One-Time Setup of Python Virtual Environment
    python -m venv env
    . env/bin/activate
    pip install wheel
    pip install -r requirements.txt
    deactivate

## Developing and Testing on a Local Machine
    Begin development:
        . env/bin/activate
        Check for a currently running db and stop it if there is one:
            pg_isready
            sudo su - postgres
            pg_ctl stop
            pg_isready
            pg_ctl start

    #
    # (... make code changes ...)
    #

    Test changes on a local machine:
        DEBUG=1 python server.py
        # (open a browser to http://localhost:5000)
        # (all code changes cause flask to restart, allowing changes to be seen just by refreshing the browser)

    End development:
        pg_ctl stop
        deactivate

install python libraries
------------------------

* run this if pip is not already installed
sudo easy_install pip

sudo easy_install psycopg2
sudo pip install pytest
sudo pip install wheel
sudo pip install -r requirements.txt

running the system
------------------

# activate virtual environment
. env/bin/activate

# run test suite
python test_all.py

# run localy accessible server flask server on port 5000
DEBUG=1 python server.py

# run globally accessible gunicorn server on port 8000
gunicorn server:app -b 0.0.0.0:8000

# run all processes defined in the Procfile locally through heroku
(specify environment variables in a file called .env)
heroku local 

How to Generate Documentation
=============================

`epydoc --html *.py -o docs`

Doesn't have to be put in "docs", that's just an example.
May have to run `sudo pip install epydoc` first.

