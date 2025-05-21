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
    if 'user_id' in session:  # Ensure session is based on user_id, not username
        return redirect("/home")

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("Missing username or password", "error")
            return redirect("/login")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id, password_hash FROM users WHERE username=?", (username,))
        user = cur.fetchone()
        conn.close()

        if user and checkPassword(username, password):  # If password matches stored hash
            session["user_id"] = user["user_id"]  # Store correct ID
            session["username"] = username
            return redirect("/home")
        else:
            flash("Invalid username or password", "error")
            return redirect("/login")

    return render_template("login.html")



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
    notifications = []

    if 'user_id' in session:
        user_id = session['user_id']
        conn = get_db_connection()
        cur = conn.cursor()

        # Fetch pending friend requests
        cur.execute("SELECT username FROM users WHERE user_id IN (SELECT user_id1 FROM friends WHERE user_id2 = ?)", (user_id,))
        friend_requests = [row["username"] for row in cur.fetchall()]
        for request in friend_requests:
            notifications.append({"type": "friend_request", "message": f"{request} sent a friend request!"})

        # Fetch pending game invites
        cur.execute("SELECT game_name FROM challengehistory WHERE user_id2 = ? AND winner_id IS NULL", (user_id,))
        game_invites = [row["game_name"] for row in cur.fetchall()]
        for invite in game_invites:
            notifications.append({"type": "game_invite", "message": f"You have a pending game in {invite}!"})

        conn.close()

    return render_template("home.html", notifications=notifications)




@app.route('/profile')
def profile():
    if 'user_id' not in session or not session['user_id']:
        return redirect(url_for('login'))  # Redirect to login if session isn't set

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
    user = cur.fetchone()

    if not user:
        return redirect(url_for('login'))  # Redirect if user not found

    leaderboards = {}
    for game in ["anagrams", "wordhunt", "wordbites"]:
        cur.execute(f"SELECT games_played, top_score FROM {game}_leaderboard WHERE user_id = ?", (user_id,))
        stats = cur.fetchone()
        if stats:
            leaderboards[game] = {"games_played": stats["games_played"], "top_score": stats["top_score"]}

    cur.execute("""
        SELECT u.username AS opponent, ch.game_name, ch.score1, ch.score2, ch.winner_id
        FROM challengehistory ch
        LEFT JOIN users u ON (ch.user_id2 = u.user_id)
        WHERE ch.user_id1 = ?
    """, (user_id,))

    challenges = [dict(row) for row in cur.fetchall()]
    conn.close()

    return render_template('profile.html',
                            user={"username": user["username"], "user_id": user_id},
                            leaderboards=leaderboards,
                            challenges=challenges)

@app.route('/game')
def game():
    return render_template("gamepage.html")



@app.route('/wordbites')
def wordbites():
    global wordbites_letter_positions
    global wordbites_words
    global wordbites_board
    global wordbites_score
    wordbites_letter_positions = {} #reset letter positions (for every game)
    wordbites_words = {} #reset words (for every game)
    wordbites_board = [['' for _ in range(8)] for _ in range(9)] #reset board (for every game)
    wordbites_score = 0 #reset score (for every game)
    all_letters = []
    with open('letters_w.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            all_letters.extend(row)
    all_letters = [l for l in all_letters if l]

    letters = []
    i=0

    while i<16:
        temp = random.choice(all_letters)
        if temp not in letters:
            letters += [temp]
            i+=1

    for i, letter in enumerate(letters):
        if letter not in wordbites_letter_positions:
            wordbites_letter_positions[letter] = i + 1

    return render_template("wordbites.html",
                            letters = letters,
                            found = wordbites_words,
                            score = wordbites_score)

@app.route("/wordbites_helper", methods=["POST"])
#happens in the background and ensures that it doesnt need to refresh
def wordbites_helper():
    global wordbites_letter_positions
    global wordbites_words
    global wordbites_board
    global wordbites_score

    data = request.get_json()
    letter = data.get("letter")
    from_box = data.get("from_box")
    to_box = data.get("to_box")

    wordbites_letter_positions[letter] = to_box

    wordbites_board = [['' for _ in range(8)] for _ in range(9)]
    for letter, pos in wordbites_letter_positions.items():
        row, col = (pos-1) // 8, (pos-1) % 8
        wordbites_board[row][col] = letter
    for row in wordbites_board:
        i = 0
        while i < len(row):
            if row[i] != '':
                start = i
                while i < len(row) and row[i] != '':
                    i += 1
                end = i
                if (start == 0 or row[start - 1] == '')
                        and (end == len(row) or row[end] == ''):
                    if end - start >= 3:
                        word = ''.join(row[start:end])
                        if word.lower() in all_words:
                            if word not in wordbites_words.keys():
                                wordbites_score += wordbites_score_calc(len(word))
                                wordbites_words[word] = wordbites_score_calc(len(word))

            else:
                i += 1

    for col in range(8):
        col_mod = [wordbites_board[row][col] for row in range(9)]
        i = 0
        while i < len(col_mod):
            if col_mod[i] != '':
                start = i
                while i < len(col_mod) and col_mod[i] != '':
                    i += 1
                end = i
                if (start == 0 or col_mod[start - 1] == '')
                        and (end == len(col_mod) or col_mod[end] == ''):
                    if end - start >= 3:
                        word = ''.join(col_mod[start:end])
                        if word.lower() in all_words:
                            if word not in wordbites_words.keys():
                                wordbites_score += wordbites_score_calc(len(word))
                                wordbites_words[word] = wordbites_score_calc(len(word))
            else:
                i += 1

    return jsonify({"status": "received",
                    "found_words": wordbites_words,
                    "score": wordbites_score})

@app.route("/wordhunt", methods=['GET', 'POST'])
def wordhunt():
    Letters = board()
    print(Letters + "test")
    return render_template('wordhunt.html',
                            letterString=Letters,
                            LetterA=Letters[0], LetterB=Letters[1],
                            LetterC=Letters[2], LetterD=Letters[3],
                            LetterE=Letters[4], LetterF=Letters[5],
                            LetterG=Letters[6], LetterH=Letters[7],
                            LetterI=Letters[8], LetterJ=Letters[9],
                            LetterK=Letters[10], LetterL=Letters[11],
                            LetterM=Letters[12], LetterN=Letters[13],
                            LetterO=Letters[14], LetterP=Letters[15])



@app.route('/anagrams')
def anagrams():

    letters = getWordSelectionAnagrams()
    return render_template("anagrams.html", letters = letters)
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
