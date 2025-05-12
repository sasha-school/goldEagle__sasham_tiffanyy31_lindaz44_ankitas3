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


@app.route("/register", methods=["GET", "POST"])# will code registering and logging forms later
def register():
    if request.method =="POST":
        username = request.form.get("username")
        password = request.form.get("password")
      

        if not username or not password:# checks if all 3 form entries were filled out
            return render_template("register.html", warning = "empty field(s)")

        #check if user has special chars
        #check for existing username
        message = addUser(username, password)
        if message:
            return render_template("login.html", warning = message)
        else:
            return redirect("/login")

@app.route('/home')
def homePage():
    return render_template("home.html")


@app.route('/anagrams')
def anagrams():
    return render_template("anagrams.html")
    


if __name__ == "__main__":
    app.run(debug=True)
