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
    build()
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

        if user_id is not None:
            if check_password(username, password):  # If user exists and password matches stored hash
                session["user_id"] = user_id  # Store correct ID
                session["username"] = username
                return redirect("/home")
            else:
                flash("Invalid username or password", "error")
                return redirect("/login")
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
        friends_list = get_friends(user_id)  # Should return list of usernames
        # friend_requests should be a list of dicts: {"user_id": ..., "username": ...}
        friend_requests = get_pending_friend_requests(user_id)
        # recent_challenges: list of strings or dicts as needed by your template
        recent_challenges = get_recent_challenges(user_id) if 'get_recent_challenges' in globals() else []
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
        user={"username": user_data, "user_id": user_id},
        leaderboards=leaderboards,
        challenges=challenges
    )


@app.route('/game')
def game():

    #html for challenge table -- could add challenges for anagrams and wordbite as well
    received_challenge = ""
    sent_challenge = ""
    

    if 'user_id' in session:
        user_id = session['user_id']
        all_wh_received = get_received_wordhunt_challenges(user_id) #received wordhunt challenges
        all_wh_sent = get_sent_wordhunt_challenges(user_id)
        print(user_id)
        print(all_wh_received)
        print(all_wh_sent)
        for row in all_wh_received:
            game_id = row[0]
            game_id = int(game_id)
            board_string = get_wordhunt_boardstring(game_id)
            link= f"/wordhunt?board={board_string}"
            sent_username = get_user(int(row[1]))
            received_score = row[4]
            if received_score is None: #if user hasn't played the game yet
                received_challenge += f'''<tr><td>Wordhunt</td><td>{sent_username} (#{row[1]})</td><td><a href="{link}"><button>Play</button></a></td></tr>'''
        for row in all_wh_sent:
            game_id = row[0]
            game_id = int(game_id)
            board_string = get_wordhunt_boardstring(game_id)
            received_user = get_user(int(row[2]))
            sent_score = row[3]
            received_score = row[4]
            if received_score is None:
                received_score = "awaiting score..."
            sent_challenge += f'''<tr><td>Wordhunt to {received_user}</td><td>{sent_score}</td><td>{received_score}</td></tr>'''
           


    return render_template("gamepage.html", received_challenge = received_challenge, sent_challenge = sent_challenge)

#lindas code
@app.route('/ana_game')
def ana_game():
    if 'user_id' in session:
        ana_user_id = session['user_id']
        ana_received_challenge = ""
        ana_sent_challenge = ""
        all_ana_received = get_received_anagrams_challenges(ana_user_id) #received anagrams challenges
        all_ana_sent = get_sent_anagrams_challenges(ana_user_id)
        for i in all_ana_received:
            ana_game_id = int(i[0])
            ana_board_string = get_anagrams_ana_string(ana_game_id)
            ana_link= f"/anagrams?board={ana_board_string}"
            ana_sent_username = get_user(int(i[1]))
            ana_received_score = i[4]
            if ana_received_score is None: #if user hasn't played the game yet
                ana_received_challenge += f'''<tr><td>Anagrams</td><td>{ana_sent_username} (#{i[1]})</td><td><a href="{ana_link}"><button>Play</button></a></td></tr>'''
        for i in all_ana_sent:
            ana_game_id = int(i[0])
            ana_board_string = get_anagrams_ana_string(ana_game_id)
            ana_received_user = get_user(int(i[2]))
            ana_sent_score = i[3]
            print("sent: " + str(ana_sent_score))
            ana_received_score = i[4]
            print("re: " + str(ana_received_score))
            if ana_received_score is None:
                ana_received_score = "awaiting score..."
            ana_sent_challenge += f'''<tr><td>Anagrams to {ana_received_user}</td><td>{ana_sent_score}</td><td>{ana_received_score}</td></tr>''' 

    return render_template("ana_gamepage.html", ana_received_challenge = ana_received_challenge, ana_sent_challenge = ana_sent_challenge)



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

    letters = [] #"unique board"
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
## from linda's code
@app.route('/send_wordbites_challenge', methods=['POST'])
def send_wordbites_challenge():
    if 'user_id' not in session:
        return jsonify({'redirect': url_for('login')})
    user_id = session['user_id']
    friend_id = request.form.get('friend_id')
    friend_username = get_user(friend_id)
    if int(friend_id) == int(user_id):
        return jsonify({'message': "you can't challenge yourself"})
    elif friend_username is None:
        return jsonify({'message': "user does not exist"})

    board_string = request.form.get('board_string')
    add_wordbites_board(user_id, board_string)
    game_id = get_wordbites_id(board_string)
    add_wordbites_challenge(user_id, friend_id, game_id)
    return jsonify({'message' : "challenge request sent"})

@app.route('/add_wb_board', methods=['POST'])
def add_wb_board():
    if 'user_id' not in session:
        return "not logged in"
    else:
        user_id = session['user_id']
        board_string = request.form.get('board_string')
        add_wordbites_board(user_id, board_string)
        #print(get_wordhunt_board(user_id))
        return "saved board"

@app.route('/update_wb_score', methods=['POST'])
def update_wb_score():
    if 'user_id' not in session:
        return "not logged in"
    else:
        user_id = session['user_id']
        board_string = request.form.get('board_string')
        game_id = get_wordbites_id(board_string)
        score = request.form.get('score')
        score = int(score)
        update_wordbites_score(user_id, game_id, score)
        update_wordbites_lb(user_id, score)
        return "saved score"

#challenge game (sender score)
@app.route('/update_wbc_score_A', methods=['POST'])
def update_wbc_score_A():
    if 'user_id' not in session:
        return "not logged in"
    else:
        board_string = request.form.get('board_string')
        game_id = get_wordbites_id(board_string)
        score = request.form.get('score')
        score = int(score)
        update_challenge_score_A_wb(game_id, score)
        return "saved score"

#receiver game (receiver score)
@app.route('/update_wbc_score_B', methods=['POST'])
def update_wbc_score_B():
    if 'user_id' not in session:
        return "not logged in"
    else:
        board_string = request.form.get('board_string')
        game_id = get_wordbites_id(board_string)
        score = request.form.get('score')
        score = int(score)
        update_challenge_score_B_wb(game_id, score)
        return "saved score"

@app.route("/wordhunt", methods=['GET', 'POST'])
def wordhunt():
    board_string = request.args.get('board')
    if board_string and len(board_string) == 16:
        Letters = board_string
    else:
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

@app.route('/add_wh_board', methods=['POST'])
def add_wh_board():
    if 'user_id' not in session:
        user_id = 0
    else:
        user_id = session['user_id']
    board_string = request.form.get('board_string')
    add_wordhunt_board(user_id, board_string)
    #print(get_wordhunt_board(user_id))
    return "saved board"

@app.route('/send_wordhunt_challenge', methods=['POST'])
def send_challenge():
    if 'user_id' not in session:
        return jsonify({'redirect': url_for('login')})
    user_id = session['user_id']
    friend_id = request.form.get('friend_id')
    friend_username = get_user(friend_id)
    print(type(user_id), user_id)
    print(type(friend_id), friend_id)
    if int(friend_id) == int(user_id):
        return jsonify({'message': "you can't challenge yourself"})
    elif friend_username is None:
        return jsonify({'message': "user does not exist"})

    board_string = request.form.get('board_string')
    add_wordhunt_board(user_id, board_string)
    game_id = get_wordhunt_id(board_string)
    add_wordhunt_challenge(user_id, friend_id, game_id)
    return jsonify({'message' : "challenge request sent"})

#solo game
@app.route('/update_wh_score', methods=['POST'])
def update_wh_score():
    if 'user_id' not in session:
        user_id = 0
    else:
        user_id = session['user_id']
    board_string = request.form.get('board_string')
    game_id = get_wordhunt_id(board_string)
    score = request.form.get('score')
    score = int(score)
    update_wordhunt_score(user_id, game_id, score)
    update_wordhunt_lb(user_id, score)
    return "saved score"

#challenge game (sender score)
@app.route('/update_whc_score_A', methods=['POST'])
def update_whc_score_A():
    if 'user_id' not in session:
        return "not logged in"
    else:
        board_string = request.form.get('board_string')
        game_id = get_wordhunt_id(board_string)
        score = request.form.get('score')
        score = int(score)
        update_challenge_score_A(game_id, score)
        return "saved score"

#receiver game (receiver score)
@app.route('/update_whc_score_B', methods=['POST'])
def update_whc_score_B():
    if 'user_id' not in session:
        return "not logged in"
    else:
        board_string = request.form.get('board_string')
        game_id = get_wordhunt_id(board_string)
        score = request.form.get('score')
        score = int(score)
        update_challenge_score_B(game_id, score)
        return "saved score"

@app.route('/add_wh_words', methods=['POST'])
def add_wh_words():
    if 'user_id' not in session:
        user_id = 0
    else:
        user_id = session['user_id']
    board_string = request.form.get('board_string')
    game_id = get_wordhunt_id(board_string)
    word = request.form.get('word')
    add_wordhunt_word(game_id, user_id, word)
    return "added word"

@app.route('/send_anagrams_challenge', methods=['POST'])
def send_challenge_ana():
    if 'user_id' not in session:
        return jsonify({'redirect': url_for('login')})
    user_id = session['user_id']
    friend_id = request.form.get('friend_id')
    ana_string = request.form.get('ana_string')
    add_anagrams_list(user_id, ana_string)
    game_id = get_anagrams_id(ana_string)
    add_anagrams_challenge(user_id, friend_id, game_id)
    return jsonify({'message' : "challenge request sent"})

@app.route('/add_ana_string', methods=['POST'])
def add_ana_board():
    if 'user_id' not in session:
        return "not logged in"
    else:
        user_id = session['user_id']
        ana_string = request.form.get('ana_string')
        add_anagrams_list(user_id, ana_string)
        #print(get_wordhunt_board(user_id))
        return "saved board"

@app.route('/endgame', methods=['POST', 'GET'])
def endgame():
    board_string = request.args.get('board_string')
    game_id = get_wordhunt_id(board_string)

    game_type = request.args.get('game_type')
    challenge = request.args.get('challenge')

    display = ""

    words_a_html = ""
    words_b_html = ""

    # get found words for wordhunt
    if challenge == 'true' and (game_type == "wordhunt"):
        wh_game_info = get_wh_challenge_info(game_id)
        words_a = sorted(get_all_words_wh(game_id, wh_game_info[1]))
        words_b = sorted(get_all_words_wh(game_id, wh_game_info[2]))

        words_a = sorted(words_a, key=len)
        words_b = sorted(words_b, key=len)

        for word in words_a:
            words_a_html += f'''<li>{word}</li>'''

        for word in words_b:
            words_b_html += f'''<li>{word}</li>'''
        
        scoreA = wh_game_info[3]
        scoreB = wh_game_info[4]

        display = f'''<div style="box-shadow: 0px 11px 10px 4px rgba(0, 0, 0, 0.4);" class="scroll-smooth overflow-y-auto rounded-lg text-3xl bg-[url(/static/img/wood.png)] w-full max-w-md h-full">
                            <h1>Score: {scoreA}</h1>
                            <ul class="list-none p-5">
                                {words_a_html}
                            </ul>
                        </div>
                        <div style="box-shadow: 0px 11px 10px 4px rgba(0, 0, 0, 0.4);" class="scroll-smooth overflow-y-auto rounded-lg text-3xl bg-[url(/static/img/wood.png)] w-full max-w-md h-full">
                            <h1>Score: {scoreB}</h4>
                            <ul class="list-none p-5">
                                {words_b_html}
                            </ul>
                        </div>'''
    if challenge == 'false':
        wh_game_info = get_wh_saved_board(game_id)
        words = sorted(get_all_words_wh(game_id, wh_game_info[1]))
        words = sorted (words, key=len)

        for word in words:
            words_a_html += f'''<li>{word}</li>'''
        score = wh_game_info[2]
        print(score)
        print(wh_game_info)
        display = f'''<div style="box-shadow: 0px 11px 10px 4px rgba(0, 0, 0, 0.4);" class="scroll-smooth overflow-y-auto rounded-lg text-3xl bg-[url(/static/img/wood.png)] w-full max-w-md h-full">
                            <h1>Score: {score}</h1>
                            <ul class="list-none p-5">
                                {words_a_html}
                            </ul>
                        </div>'''

    return render_template("endpage.html", display=display)


@app.route('/add_ana_words', methods=['POST'])
def add_ana_words():
    if 'user_id' not in session:
        return "not logged in"
    else:
        user_id = session['user_id']
        ana_string = request.form.get('ana_string')
        game_id = get_anagrams_id(ana_string)
        word = request.form.get('word')
        add_anagrams_word(game_id, user_id, word)
        return "added word"


@app.route('/update_ana_score', methods=['POST'])
def update_ana_score():
    if 'user_id' not in session:
        return "not logged in"
    else:
        user_id = session['user_id']
        ana_string = request.form.get('ana_string')
        game_id = get_anagrams_id(ana_string)
        score = request.form.get('totPoint')
        score = int(score)
        update_anagrams_score(user_id, game_id, score)
        update_anagrams_lb(user_id, score)
        return "saved score"


@app.route('/update_ana_score_A', methods=['POST'])
def update_ana_score_A():
    if 'user_id' not in session:
        return "not logged in"
    else:
        ana_string = request.form.get('ana_string')
        game_id = get_anagrams_id(ana_string)
        score = request.form.get('totPoint')
        score = int(score)
        print(score)
        update_challenge_score_AnaA(game_id, score)
        return "saved score"

#receiver game (receiver score)
@app.route('/update_ana_score_B', methods=['POST'])
def update_ana_score_B():
    if 'user_id' not in session:
        return "not logged in"
    else:
        ana_string = request.form.get('ana_string')
        game_id = get_anagrams_id(ana_string)
        score = request.form.get('totPoint')
        score = int(score)
        print(score)
        update_challenge_score_AnaB(game_id, score)
        return "saved score"


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
