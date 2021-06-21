import sqlite3
from utils import get_time

def create_users_db():
    '''Create username and password database'''
    con = sqlite3.connect('users.db')
    cur = con.cursor()
    cur.execute('''CREATE TABLE Users (
                Key INTEGER PRIMARY KEY,
                Username TEXT UNIQUE NOT NULL,
                Password TEXT NOT NULL,
                Privileged INTEGER NOT NULL
    );''')

    con.commit()
    con.close()


def create_chat_db():
    con = sqlite3.connect('chat.db')
    cur = con.cursor()
    cur.execute('''CREATE TABLE Private_Messages (
                Key INTEGER PRIMARY KEY,
                Message TEXT NOT NULL,
                Sender TEXT NOT NULL,
                Recipient TEXT NOT NULL,
                Timestamp INTEGER NOT NULL,
                ID INTEGER NOT NULL

    );''')

    cur.execute('''CREATE TABLE Tickers (
                Key INTEGER PRIMARY KEY,
                Room TEXT NOT NULL,
                Username TEXT NOT NULL,
                Ticker TEXT NOT NULL

    );''')

    con.commit()
    con.close()

#TODO AT SCALE this needs to be a seperate thread with QUEUE all db (Acctually maybe not because twisted is only one thread)
#TODO dont store passwords in plain text use sha-256
def login_user(username, password):
    '''Sqlite function for managing signing in and creating new user entrys in the database

    If the username does not exist a new entry is created. If the user does exist and the
    password is correct then the string 'success' is returned. If the password does not
    match the string 'failure' is sent
    '''

    con = sqlite3.connect('users.db')
    cur = con.cursor()

    sql_code = ('''SELECT * FROM Users WHERE Username = ?;''')
    args = (username,)
    cur.execute(sql_code, args)
    search_result = cur.fetchone()

    if search_result == None:
        sql_code = ('''INSERT INTO Users(Username,Password,Privileged)
                    VALUES(?,?,0);''')
        args = (username, password,)
        cur.execute(sql_code, args)
        con.commit()
        con.close()
        return ['success', 0]

    elif search_result[2] == password:
        con.close()
        return ['success', search_result[3]]

    elif search_result[2] != password:
        con.close()
        return ['failure']


def user_exist(username):
    con = sqlite3.connect('users.db')
    cur = con.cursor()

    sql_code = ('''SELECT * FROM Users WHERE Username = ?;''')
    args = (username,)
    cur.execute(sql_code, args)
    search_result = cur.fetchone()
    con.close()

    if search_result == None:
        return False

    else:
        return True


def get_saved_private_messages(username):
    con = sqlite3.connect('chat.db')
    cur = con.cursor()

    sql_code = ('''SELECT * FROM Private_Messages WHERE Recipient = ?;''')
    args = (username,)
    cur.execute(sql_code, args)

    search_results = cur.fetchall()

    con.close()

    pms = []

    for search_result in search_results:
        pm = {}
        pm['message'] = search_result[1]
        pm['username'] = search_result[2]
        pm['timestamp'] = search_result[4]
        pm['ID'] = search_result[5]
        pms.append(pm)

    return pms


def save_private_message(message, sender, recipient, timestamp, ID):
    con = sqlite3.connect('chat.db')
    cur = con.cursor()

    sql_code = ('''INSERT INTO Private_Messages(Message,Sender,Recipient,Timestamp,ID)
                VALUES(?,?,?,?,?);''')
    args = (message, sender, recipient, timestamp, ID,)
    cur.execute(sql_code, args)
    con.commit()
    con.close()


def delete_private_message(recipient, ID):
    con = sqlite3.connect('chat.db')
    cur = con.cursor()

    sql_code = ('''DELETE FROM Private_Messages WHERE Recipient = ? AND ID = ?;''')
    args = (recipient, ID,)
    cur.execute(sql_code, args)
    con.commit()
    con.close()


def save_ticker(username, room, ticker):
    con = sqlite3.connect('chat.db')
    cur = con.cursor()

    sql_code = ('''SELECT * FROM Tickers WHERE Username = ? AND Room = ?;''')
    args = (username, room,)
    cur.execute(sql_code, args)
    search_result = cur.fetchone()

    if search_result == None:
        sql_code = ('''INSERT INTO Tickers(Room,Username,Ticker)
                    VALUES(?,?,?);''')
        args = (room, username, ticker,)
        cur.execute(sql_code, args)
        con.commit()
        con.close()

    else:
        sql_code = ('''UPDATE Tickers
                    SET Ticker = ?
                    WHERE Username = ? AND Room = ?;''')
        args = (ticker, username, room,)
        cur.execute(sql_code, args)
        con.commit()
        con.close()
