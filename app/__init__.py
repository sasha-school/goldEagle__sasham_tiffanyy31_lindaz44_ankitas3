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

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect("/home")
    elif request.method == 'POST':
        return redirect("/auth")
    return render_template("login.html")


if __name__ == "__main__":
    app.run(port = 5001,debug=True)
