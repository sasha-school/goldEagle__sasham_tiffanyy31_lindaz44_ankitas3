
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
print("DB_PATH:", DB_PATH)

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


def checkPassword(username, password):
    users = sqlite3.connect(DB_PATH)
    c = users.cursor()
    c.execute("SELECT password_hash FROM users WHERE username=?", (username,))
    res = c.fetchone()
    if (password != res[0]):
        return "Invalid login; please try again."
    return True


# with open('../letters7.txt', 'r') as file:
#     lines = [line.strip() for line in file]

# with open("wordList.json", "w") as f:
#     json.dump(lines, f)
