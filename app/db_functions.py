
import json
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

#DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')

#corresponding integers
anagrams =1
wordhunt =2
wordbites =3


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DB_DIR, exist_ok=True)  # Make sure the folder exists

DB_PATH = os.path.join(DB_DIR, 'database.db')

def build():
    create_tables()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
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

#store letters so they stay same upon reload
    conn.commit()
    conn.close()


def addUser(username, password):
    users = sqlite3.connect(DB_PATH)
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
    users = sqlite3.connect(DB_PATH)
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
    return user
# with open('../letters7.txt', 'r') as file:
#     lines = [line.strip() for line in file]

# with open("wordList.json", "w") as f:
#     json.dump(lines, f)
