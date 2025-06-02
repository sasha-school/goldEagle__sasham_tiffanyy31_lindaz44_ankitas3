import os, sys

import urllib.parse
import sqlite3
import requests
import datetime
import calendar
import csv

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from dateutil.parser import parse
from functools import wraps
from calendar import monthrange, day_name


try:
    from app.anagrams import *
except:
    from anagrams import *

try:
    from app.wordhunt import *
except:
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

        user_id = get_user_id(username)

        if user_id is not None and check_password(username, password):  # If user exists and password matches stored hash
            session["user_id"] = user_id["user_id"]  # Store correct ID
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
            flash("Empty field(s)", "error")
            return render_template("register.html")

        message = addUser(username, password)
        if message:
            flash(message, "error")
            return render_template("register.html")  # Make sure it renders the register page with error
        else:
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))  # Proper redirect after successful registration

    return render_template("register.html")  # Ensures a response is returned for GET requests




@app.route("/home")
def home():
    # Assume user_id is fetched from session if logged in
    user_id = session.get("user_id")
    if user_id:
        # Fetch stats from DB
        leaderboards, _ = get_profile(user_id)
        highest_scores = {
            "anagrams": leaderboards.get("anagrams", {}).get("top_score"),
            "wordhunt": leaderboards.get("wordhunt", {}).get("top_score"),
            "wordbites": leaderboards.get("wordbites", {}).get("top_score"),
        }
        games_played = {
            "anagrams": leaderboards.get("anagrams", {}).get("games_played"),
            "wordhunt": leaderboards.get("wordhunt", {}).get("games_played"),
            "wordbites": leaderboards.get("wordbites", {}).get("games_played"),
        }
        # Fetch friends and requests
        friends_list = [...]  # Query your DB
        friend_requests = [...]  # Query your DB
        recent_challenges = [...]  # Query your DB
    else:
        highest_scores = {"anagrams": None, "wordhunt": None, "wordbites": None}
        games_played = {"anagrams": None, "wordhunt": None, "wordbites": None}
        friends_list = []
        friend_requests = []
        recent_challenges = []

    return render_template(
        "home.html",
        highest_scores=highest_scores,
        games_played=games_played,
        friends_list=friends_list,
        friend_requests=friend_requests,
        recent_challenges=recent_challenges,
    )


@app.route('/profile')
def profile():
    if 'user_id' not in session or not session['user_id']:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user_data = get_user(user_id)
    if not user_data:
        return redirect(url_for('login'))

    leaderboards, challenges = get_profile(user_id)

    # Ensure leaderboards is a dict of dicts with keys 'games_played' and 'top_score'
    # Ensure challenges is a list of dicts with keys: opponent, game_name, score1, score2, winner_id

    return render_template(
        'profile.html',
        user={"username": user_data["username"], "user_id": user_id},
        leaderboards=leaderboards,
        challenges=challenges
    )


@app.route('/game')
def game():
    return render_template("gamepage.html")

wordbites_letter_positions = {}
wordbites_words = {}
wordbites_board = [['' for _ in range(8)] for _ in range(9)]
wordbites_score = 0
all_letters = []
all_words = []
with open('letters7.txt', 'r') as text:
    for word in text:
        all_words += [word[:-1]]

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
                if (start == 0 or row[start - 1] == '') and (end == len(row) or row[end] == ''):
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
                if (start == 0 or col_mod[start - 1] == '') and (end == len(col_mod) or col_mod[end] == ''):
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

def wordbites_score_calc(len):
    key = {3: 100, 4: 400, 5: 800, 6:1400, 7:1800, 8:2200, 9:2600} #from actual game
    if len in key:
        return key[len]
    return 100

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
    if 'user_id' not in session or not session['user_id']:
        return redirect(url_for('login'))

    user_id = session['user_id']
    userName = get_user(user_id)
    if not userName:
        return redirect(url_for('login'))
    letters = getWordSelectionAnagrams()
    return render_template("anagrams.html", letters = letters, userName = userName)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/friends')
def friends():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    friends_list = get_friends(user_id)
    pending_requests = get_pending_friend_requests(user_id)
    return render_template('friends.html', friends=friends_list, requests=pending_requests)

@app.route('/send_request/<int:to_user_id>')
def send_request(to_user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    from_user_id = session['user_id']
    message = send_friend_request(from_user_id, to_user_id)
    if message:
        flash(message)
    return redirect(url_for('friends'))

@app.route('/send_request', methods=['POST'])
def send_request_dynamic():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    from_user_id = session['user_id']
    to_user_id = request.form.get('to_user_id', type=int)
    if to_user_id is None:
        flash("Invalid user ID")
        return redirect(url_for('friends'))
    message = send_friend_request(from_user_id, to_user_id)
    if message:
        flash(message)
    return redirect(url_for('friends'))


@app.route('/respond_request/<int:from_user_id>/<action>')
def respond_request(from_user_id, action):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    accept = (action == 'accept')
    respond_to_friend_request(user_id, from_user_id, accept)
    return redirect(url_for('friends'))

@app.route('/remove_friend/<int:friend_id>')
def remove_friend_route(friend_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    remove_friend(user_id, friend_id)
    return redirect(url_for('friends'))

@app.route('/send_wordhunt_challenge', methods=['POST'])
def send_challenge():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    friend_id = request.form.get('friend_id')
    board_string = request.form.get('board_string')
    game_id = get_wordhunt_id(board_string)
    add_wordhunt_challenge(user_id, friend_id, game_id)
    return "sent request"

@app.route('/add_wh_board', methods=['POST'])
def add_wh_board():
    if 'user_id' not in session:
        return "not logged in"
    else:
        user_id = session['user_id']
        board_string = request.form.get('board_string')
        add_wordhunt_board(user_id, board_string)
        #print(get_wordhunt_board(user_id))
        return "saved board"

@app.route('/add_wh_words', methods=['POST'])
def add_wh_words():
    if 'user_id' not in session:
        return "not logged in"
    else:
        user_id = session['user_id']
        board_string = request.form.get('board_string')
        game_id = get_wordhunt_id(board_string)
        word = request.form.get('word')
        add_wordhunt_word(game_id, user_id, word)
        return "added word"

def get_notifications(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    notifications = []
    c.execute("SELECT username FROM users WHERE user_id IN (SELECT user_id1 FROM friends WHERE user_id2 = ?)", (user_id,))
    friend_requests = [row["username"] for row in c.fetchall()]
    for request in friend_requests:
        notifications.append({"type": "friend_request", "message": f"{request} sent a friend request!"})

    # Fetch pending game invites
    c.execute("SELECT game_name FROM challengehistory WHERE user_id2 = ? AND winner_id IS NULL", (user_id,))
    game_invites = [row["game_name"] for row in c.fetchall()]
    for invite in game_invites:
        notifications.append({"type": "game_invite", "message": f"You have a pending game in {invite}!"})

    conn.close()
    return notifications

if __name__ == "__main__":
    build()
    app.run(host="0.0.0.0", port=8000, debug=True)
