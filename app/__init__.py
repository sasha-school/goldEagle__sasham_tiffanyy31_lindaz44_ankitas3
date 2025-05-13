import os, sys

import urllib.parse
import sqlite3
import requests
import datetime
import calendar

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from dateutil.parser import parse
from functools import wraps
from calendar import monthrange, day_name


from db_functions import *
from anagrams import *
from wordhunt import *

try:
    from app.db_functions import *
except:
    from db_functions import *


# adding config.py to search path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# flask app initializing
app = Flask(__name__)


# sessions
secret = os.urandom(32)
app.secret_key = secret

@app.route('/')
def checkSession():
    if 'username' in session:
        return redirect("/home")
    return redirect("/login")


@app.route('/login', methods=['GET', 'POST'])
def login():
    build()
    if 'username' in session:
        return redirect("/home")

    if request.method =="POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("Missing username or password", "error")
            return redirect("/login")

        if checkPassword(username, password):# if password is correct, given user exists
            session["username"] = username# adds user to session
            return redirect("/home")

        else:# if password isnt correct
            flash("Invalid username or password", "error")
            return redirect("/login")

    return render_template("login.html")# if GET request, just renders login page


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return render_template("register.html", warning="Empty field(s)")

        message = addUser(username, password)
        if message:
            return render_template("register.html", warning=message)  # Make sure it renders the register page with error
        else:
            return redirect(url_for("login"))  # Proper redirect after successful registration

    return render_template("register.html")  # Ensures a response is returned for GET requests

@app.route('/home')
def home():
    return render_template("home.html")

@app.route('/game')
def game():
    return render_template("gamepage.html")

@app.route('/wordbites')
def wordbites():
    return render_template("wordbites.html")

@app.route('/wordhunt')
def wordhunt():
    return render_template("wordhunt.html")

@app.route('/anagrams')
def anagrams():

    letters = getWordSelectionAnagrams()
    return render_template("anagrams.html", letters = letters)

    return render_template("anagrams.html")

@app.route("/wordhunt", methods=['GET', 'POST'])
def main():
    Letters = board()
    return render_template('wordhunt.html', LetterA=Letters[0], LetterB=Letters[1], LetterC=Letters[2], LetterD=Letters[3], LetterE=Letters[4], LetterF=Letters[5], LetterG=Letters[6], LetterH=Letters[7], LetterI=Letters[8], LetterJ=Letters[9], LetterK=Letters[10], LetterL=Letters[11], LetterM=Letters[12], LetterN=Letters[13], LetterO=Letters[14], LetterP=Letters[15])


if __name__ == "__main__":
    app.run(debug=True)
