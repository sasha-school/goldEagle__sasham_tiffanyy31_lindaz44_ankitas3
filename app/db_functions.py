
import sqlite3

USER_FILE = "db_functions.db"

def build():
    createUsers()

def createUsers():
    users = sqlite3.connect(USER_FILE)
    c = users.cursor()
    command = "CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)"
    c.execute(command)
    users.commit()


def addUser(username, password, city):
    users = sqlite3.connect(USER_FILE)
    goodcharas = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ12345678910._-")
    if set(username).difference(goodcharas) or set(password).difference(goodcharas):
        return "There are special characters in the username or password."
    c = users.cursor()
    if (c.execute("SELECT 1 FROM users WHERE username=?", (username,))).fetchone() == None:
        c.execute("INSERT INTO users (username, password, city, wordle, streak) VALUES (?, ?, ?, ?, ?)", (username, password, city, 0, 0))
        users.commit()
        return
    return "Username taken."


def checkPassword(username, password):
    users = sqlite3.connect(USER_FILE)
    c = users.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    res = c.fetchone()
    if (password != res[0]):
        return "Invalid login; please try again."
    return True
