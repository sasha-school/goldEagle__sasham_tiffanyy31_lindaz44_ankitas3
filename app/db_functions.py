import json
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

# corresponding integers
anagrams = 1
wordhunt = 2
wordbites = 3

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DB_DIR, exist_ok=True)  # Make sure the folder exists

DB_PATH = os.path.join(DB_DIR, 'database.db')

def build():
    create_tables()

def get_db_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
    except:
        DB_DIR_droplet = os.path.join(BASE_DIR, "app.data")
        conn = sqlite3.connect(DB_DIR_droplet)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS anagrams_leaderboard(
            user_id INTEGER NOT NULL,
            games_played INTEGER NOT NULL,
            top_score INTEGER NOT NULL
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS wordhunt_leaderboard(
            user_id INTEGER NOT NULL,
            games_played INTEGER NOT NULL,
            top_score INTEGER NOT NULL
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS wordbites_leaderboard(
            user_id INTEGER NOT NULL,
            games_played INTEGER NOT NULL,
            top_score INTEGER NOT NULL
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS friends(
            user_id1 INTEGER NOT NULL,
            user_id2 INTEGER NOT NULL
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS challengehistory(
            challenge_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id1 INTEGER NOT NULL,
            user_id2 INTEGER,
            game_name INTEGER NOT NULL,
            winner_id INTEGER,
            score1 INTEGER NOT NULL,
            score2 INTEGER,
            board TEXT NOT NULL
        );
    ''')

    # You may want to create the friend_requests table if not already present
    cur.execute('''
        CREATE TABLE IF NOT EXISTS friend_requests(
            from_user_id INTEGER NOT NULL,
            to_user_id INTEGER NOT NULL
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS wordhunt_boards(
            game_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            board_string TEXT NOT NULL,
            score INTEGER
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS wordhunt_found_words(
            game_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            word TEXT NOT NULL
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS wordhunt_challenge_requests(
            game_id INTEGER NOT NULL,
            from_user_id INTEGER NOT NULL,
            to_user_id INTEGER NOT NULL,
            from_user_score INTEGER,
            to_user_score INTEGER
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS anagrams_boards(
            game_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ana_string TEXT NOT NULL,
            score INTEGER
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS anagrams_found_words(
            game_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            word TEXT NOT NULL
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS anagrams_challenge_requests(
            game_id INTEGER NOT NULL,
            from_user_id INTEGER NOT NULL,
            to_user_id INTEGER NOT NULL,
            from_user_score INTEGER,
            to_user_score INTEGER
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS wordbites_boards(
            game_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            board_string TEXT NOT NULL,
            score INTEGER
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS wordbites_challenge_requests(
            game_id INTEGER NOT NULL,
            from_user_id INTEGER NOT NULL,
            to_user_id INTEGER NOT NULL,
            from_user_score INTEGER,
            to_user_score INTEGER
        );
    ''')

    conn.commit()
    conn.close()

def addUser(username, password):
    users = get_db_connection()
    goodcharas = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ12345678910._-")
    if set(username).difference(goodcharas) or set(password).difference(goodcharas):
        return "There are special characters in the username or password."
    c = users.cursor()
    if (c.execute("SELECT 1 FROM users WHERE username=?", (username,))).fetchone() == None:
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password))
        users.commit()
        return
    return "Username taken."

def check_password(username, password):
    users = get_db_connection()
    c = users.cursor()
    c.execute("SELECT password_hash FROM users WHERE username=?", (username,))
    res = c.fetchone()
    if (password != res[0]):
        return "Invalid login; please try again."
    return True

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

def get_profile(user_id):
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()

    if not user:
        return redirect(url_for('login'))  # Redirect if user not found

    leaderboards = {}
    for game in ["anagrams", "wordhunt", "wordbites"]:
        c.execute(f"SELECT games_played, top_score FROM {game}_leaderboard WHERE user_id = ?", (user_id,))
        stats = c.fetchone()
        if stats:
            leaderboards[game] = {"games_played": stats["games_played"], "top_score": stats["top_score"]}

    c.execute("""
        SELECT u.username AS opponent, ch.game_name, ch.score1, ch.score2, ch.winner_id
        FROM challengehistory ch
        LEFT JOIN users u ON (ch.user_id2 = u.user_id)
        WHERE ch.user_id1 = ?
    """, (user_id,))

    challenges = [dict(row) for row in c.fetchall()]
    conn.close()
    return leaderboards, challenges

def get_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
    user = cur.fetchone()
    conn.close()
    if user is None:
        return None
    return user['username']

def get_user_id(username):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE username=?", (username,))
    user_id = cur.fetchone()
    conn.close()
    if user_id is None:
        return None
    return user_id['user_id']

def send_friend_request(from_user_id, to_user_id):
    if from_user_id == to_user_id:
        return "You cannot send a friend request to yourself."
    conn = get_db_connection()
    c = conn.cursor()
    # Check if already friends
    c.execute("SELECT 1 FROM friends WHERE (user_id1=? AND user_id2=?) OR (user_id1=? AND user_id2=?)",
              (from_user_id, to_user_id, to_user_id, from_user_id))
    if c.fetchone():
        conn.close()
        return "You are already friends."
    # Check if request already sent
    c.execute("SELECT 1 FROM friend_requests WHERE from_user_id=? AND to_user_id=?", (from_user_id, to_user_id))
    if c.fetchone():
        conn.close()
        return "Friend request already sent."
    # Insert friend request
    c.execute("INSERT INTO friend_requests (from_user_id, to_user_id) VALUES (?, ?)", (from_user_id, to_user_id))
    conn.commit()
    conn.close()
    return None

def get_friends(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT u.user_id, u.username FROM users u
        WHERE u.user_id IN (
            SELECT CASE
                WHEN user_id1=? THEN user_id2
                WHEN user_id2=? THEN user_id1
            END
            FROM friends
            WHERE user_id1=? OR user_id2=?
        )
    """, (user_id, user_id, user_id, user_id))
    friends = [{"user_id": row["user_id"], "username": row["username"]} for row in c.fetchall()]
    conn.close()
    return friends

def get_pending_friend_requests(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT fr.from_user_id, u.username
        FROM friend_requests fr
        JOIN users u ON fr.from_user_id = u.user_id
        WHERE fr.to_user_id=?
    """, (user_id,))
    requests = [{"user_id": row["from_user_id"], "username": row["username"]} for row in c.fetchall()]
    conn.close()
    return requests

def respond_to_friend_request(user_id, from_user_id, accept):
    conn = get_db_connection()
    c = conn.cursor()
    if accept:
        # Add to friends table
        c.execute("INSERT INTO friends (user_id1, user_id2) VALUES (?, ?)", (user_id, from_user_id))
    # Remove the friend request
    c.execute("DELETE FROM friend_requests WHERE from_user_id=? AND to_user_id=?", (from_user_id, user_id))
    conn.commit()
    conn.close()

def remove_friend(user_id, friend_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        DELETE FROM friends
        WHERE (user_id1=? AND user_id2=?) OR (user_id1=? AND user_id2=?)
    """, (user_id, friend_id, friend_id, user_id))
    conn.commit()
    conn.close()

#------------------------------------- WORDHUNT -----------------------------------------

def add_wordhunt_challenge(from_user_id, to_user_id, game_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO wordhunt_challenge_requests (game_id, from_user_id, to_user_id) VALUES (?, ?, ?)", (game_id, from_user_id, to_user_id))
    conn.commit()
    conn.close()

def get_sent_wordhunt_challenges(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT game_id, from_user_id, to_user_id, from_user_score, to_user_score FROM wordhunt_challenge_requests WHERE from_user_id = ?", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [list(row) for row in rows]

def get_received_wordhunt_challenges(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT game_id, from_user_id, to_user_id, from_user_score, to_user_score FROM wordhunt_challenge_requests WHERE to_user_id = ?", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [list(row) for row in rows]

def get_wh_saved_board(game_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT game_id, user_id, score FROM wordhunt_boards WHERE game_id = ?", (game_id,))
    row = c.fetchone()
    conn.close()
    return list(row)
 
def get_wh_challenge_info(game_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT game_id, from_user_id, to_user_id, from_user_score, to_user_score FROM wordhunt_challenge_requests WHERE game_id = ?", (game_id,))
    row = c.fetchone()
    conn.close()
    return list(row)

def get_wordhunt_boardstring(game_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT board_string FROM wordhunt_boards WHERE game_id = ?", (game_id,))
    row = c.fetchone()
    conn.close()
    return row["board_string"]

#inital first user score after sending
def update_challenge_score_A(game_id, from_user_score):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE wordhunt_challenge_requests SET from_user_score = ? WHERE game_id = ?", (from_user_score, game_id))
    conn.commit()
    conn.close()

#updates second user score after recieving
def update_challenge_score_B(game_id, to_user_score):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE wordhunt_challenge_requests SET to_user_score = ? WHERE game_id = ?", (to_user_score, game_id))
    conn.commit()
    conn.close()

def add_wordhunt_board(user_id, board_string):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO wordhunt_boards (board_string, user_id) VALUES (?, ?)", (board_string, user_id))
    conn.commit()
    conn.close()

def update_wordhunt_score(user_id, game_id, score):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE wordhunt_boards SET score = ? WHERE game_id = ? AND user_id = ?", (score, game_id, user_id))
    conn.commit()
    conn.close()

def get_wordhunt_id(board_string):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT game_id FROM wordhunt_boards WHERE board_string = ?", (board_string,))
    row = c.fetchone()
    conn.close()
    return row["game_id"]

def add_wordhunt_word(game_id, user_id, word):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO wordhunt_found_words (game_id, user_id, word) VALUES (?, ?, ?)", (game_id, user_id, word))
    conn.commit()
    conn.close()

def get_all_words_wh (game_id, user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT word FROM wordhunt_found_words WHERE game_id = ? AND user_id = ?", (game_id, user_id))
    rows = c.fetchall()
    words = [row['word'] for row in rows] #gets the word from each row, lists of words
    conn.close()
    return words

def update_wordhunt_lb (user_id, score):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT games_played, top_score FROM wordhunt_leaderboard WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row is None:
        c.execute("INSERT INTO wordhunt_leaderboard (user_id, games_played, top_score) VALUES (?, ?, ?)", (user_id, 1, score))
    else:
        games_played, top_score = row["games_played"], row["top_score"]
        c.execute("UPDATE wordhunt_leaderboard SET games_played = games_played + 1 WHERE user_id = ?", (user_id,))
        if (score >= top_score):
                c.execute("UPDATE wordhunt_leaderboard SET top_score = ? WHERE user_id = ?", (score, user_id))
    conn.commit()
    conn.close()
#------------------------------------- ANAGRAM -----------------------------------------

def add_anagrams_challenge(from_user_id, to_user_id, game_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO anagrams_challenge_requests (game_id, from_user_id, to_user_id) VALUES (?, ?, ?)", (game_id, from_user_id, to_user_id))
    conn.commit()
    conn.close()


def get_received_anagrams_challenges(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT game_id, from_user_id, to_user_id, from_user_score, to_user_score FROM anagrams_challenge_requests WHERE to_user_id = ?", (user_id,))
    row = c.fetchall()
    conn.close()
    return [list(row) for row in row]

def get_sent_anagrams_challenges(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT game_id, from_user_id, to_user_id, from_user_score, to_user_score FROM anagrams_challenge_requests WHERE from_user_id = ?", (user_id,))
    row = c.fetchall()
    conn.close()
    return [list(row) for row in row]

def get_anagrams_ana_string(game_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT ana_string FROM anagrams_boards WHERE game_id = ?", (game_id,))
    row = c.fetchone()
    conn.close()
    return row["ana_string"]

def update_challenge_score_AnaA(game_id, from_user_score):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE anagrams_challenge_requests SET from_user_score = ? WHERE game_id = ?", (from_user_score, game_id))
    conn.commit()
    conn.close()

#updates second user score after recieving
def update_challenge_score_AnaB(game_id, to_user_score):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE anagrams_challenge_requests SET to_user_score = ? WHERE game_id = ?", (to_user_score, game_id))
    conn.commit()
    conn.close()

def add_anagrams_list(user_id, ana_string):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO anagrams_boards (ana_string, user_id) VALUES (?, ?)", (ana_string, user_id))
    conn.commit()
    conn.close()

def update_anagrams_score(user_id, game_id, score):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE anagrams_boards SET score = ? WHERE game_id = ? AND user_id = ?", (score, game_id, user_id))
    conn.commit()
    conn.close()


def get_anagrams_id(ana_string):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT game_id FROM anagrams_boards WHERE ana_string = ?", (ana_string,))
    row = c.fetchone()
    conn.close()
    return row["game_id"]

def add_anagrams_word(game_id, user_id, word):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO anagrams_found_words (game_id, user_id, word) VALUES (?, ?, ?)", (game_id, user_id, word))
    conn.commit()
    conn.close()

def get_all_words_ana(game_id, user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT word FROM anagrams_found_words WHERE game_id = ? AND user_id = ?", (game_id, user_id))
    rows = c.fetchall()
    words = [row['word'] for row in rows] #gets the word from each row, lists of words
    conn.close()
    return words

def update_anagrams_lb (user_id, score):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT games_played, top_score FROM anagrams_leaderboard WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row is None:
        c.execute("INSERT INTO anagrams_leaderboard (user_id, games_played, top_score) VALUES (?, ?, ?)", (user_id, 1, score))
    else:
        games_played, top_score = row["games_played"], row["top_score"]
        c.execute("UPDATE anagrams_leaderboard SET games_played = games_played + 1 WHERE user_id = ?", (user_id,))
        if (score >= top_score):
                c.execute("UPDATE anagrams_leaderboard SET top_score = ? WHERE user_id = ?", (score, user_id))
    conn.commit()
    conn.close()

#------------------------------------- WORDBITE -----------------------------------------

def add_wordbites_board(user_id, board_string):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO wordbites_boards (board_string, user_id) VALUES (?, ?)", (board_string, user_id))
    conn.commit()
    conn.close()

def get_wordbites_id(board_string):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT game_id FROM wordbites_boards WHERE board_string = ?", (board_string,))
    row = c.fetchone()
    conn.close()
    return row["game_id"]

def add_wordbites_challenge(from_user_id, to_user_id, game_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO wordbites_challenge_requests (game_id, from_user_id, to_user_id) VALUES (?, ?, ?)", (game_id, from_user_id, to_user_id))
    conn.commit()
    conn.close()

def get_sent_wordbites_challenges(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT game_id, from_user_id, to_user_id, from_user_score, to_user_score FROM wordbites_challenge_requests WHERE from_user_id = ?", (user_id,))
    row = c.fetchall()
    conn.close()
    return [list(row) for row in row]

def get_received_wordbites_challenges(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT game_id, from_user_id, to_user_id, from_user_score, to_user_score FROM wordbites_challenge_requests WHERE to_user_id = ?", (user_id,))
    row = c.fetchall()
    conn.close()
    return [list(row) for row in row]

def get_wordbites_boardstring(game_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT board_string FROM wordbites_boards WHERE game_id = ?", (game_id,))
    row = c.fetchone()
    conn.close()
    return row["board_string"]

def update_wordbites_score(user_id, game_id, score):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE wordbites_boards SET score = ? WHERE game_id = ? AND user_id = ?", (score, game_id, user_id))
    conn.commit()
    conn.close()

def update_wordbites_lb (user_id, score):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT games_played, top_score FROM wordbites_leaderboard WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row is None:
        c.execute("INSERT INTO wordbites_leaderboard (user_id, games_played, top_score) VALUES (?, ?, ?)", (user_id, 1, score))
    else:
        games_played, top_score = row["games_played"], row["top_score"]
        c.execute("UPDATE wordbites_leaderboard SET games_played = games_played + 1 WHERE user_id = ?", (user_id,))
        if (score >= top_score):
                c.execute("UPDATE wordbites_leaderboard SET top_score = ? WHERE user_id = ?", (score, user_id))
    conn.commit()
    conn.close()


#inital first user score after sending
def update_challenge_score_A_wb(game_id, from_user_score):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE wordbites_challenge_requests SET from_user_score = ? WHERE game_id = ?", (from_user_score, game_id))
    conn.commit()
    conn.close()

#updates second user score after recieving
def update_challenge_score_B_wb(game_id, to_user_score):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE wordbites_challenge_requests SET to_user_score = ? WHERE game_id = ?", (to_user_score, game_id))
    conn.commit()
    conn.close()
