import sqlite3
from utils import get_time

def create_db():
    '''Creates database'''
    con = sqlite3.connect('sunseek.db')
    cur = con.cursor()
    cur.execute('''CREATE TABLE Users (
                Key INTEGER PRIMARY KEY,
                Username TEXT UNIQUE NOT NULL,
                Password TEXT NOT NULL,
                Privileged INTEGER NOT NULL,
                Banned INTEGER NOT NULL
    );''')

    cur.execute('''CREATE TABLE Banned_IPs (
                Key INTEGER PRIMARY KEY,
                IP TEXT UNIQUE NOT NULL
    );''')

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

    cur.execute('''CREATE TABLE Banned_Room_Names (
                Key INTEGER PRIMARY KEY,
                Room TEXT NOT NULL

    );''')

    con.commit()
    con.close()


#TODO AT SCALE this needs to be a seperate thread with QUEUE all db (Acctually maybe not because twisted is only one thread)
#TODO dont store passwords in plain text use sha-256
def login_user(username, password, private_server):
    '''Sqlite function for managing signing in and creating new user entrys in the database

    If the username does not exist a new entry is created. If the user does exist and the
    password is correct then the string 'success' is returned. If the password does not
    match the string 'failure' is sent
    '''

    con = sqlite3.connect('sunseek.db')
    cur = con.cursor()

    sql_code = ('''SELECT * FROM Users WHERE Username = ?;''')
    args = (username,)
    cur.execute(sql_code, args)
    search_result = cur.fetchone()

    if search_result == None and private_server == False:
        sql_code = ('''INSERT INTO Users(Username,Password,Privileged,Banned)
                    VALUES(?,?,0,0);''')
        args = (username, password,)
        cur.execute(sql_code, args)
        con.commit()
        con.close()
        return ['success', 0]

    elif search_result[2] == password:
        con.close()
        if search_result[4] == 0:
            return ['success', search_result[3]]
        elif search_result[4] == 1:
            return ['failure', 'Banned']

    elif search_result[2] != password:
        con.close()
        return ['failure', 'Wrong Password']


def user_exist(username):
    con = sqlite3.connect('sunseek.db')
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
    con = sqlite3.connect('sunseek.db')
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


def save_private_message(message, sender, recipient, timestamp, ID, max_pms):
    con = sqlite3.connect('sunseek.db')
    cur = con.cursor()

    sql_code = ('''SELECT * FROM Private_Messages WHERE Recipient = ?;''')
    args = (recipient,)
    cur.execute(sql_code, args)
    search_results = cur.fetchall()

    if len(search_results) < max_pms:
        sql_code = ('''INSERT INTO Private_Messages(Message,Sender,Recipient,Timestamp,ID)
                    VALUES(?,?,?,?,?);''')
        args = (message, sender, recipient, timestamp, ID,)
        cur.execute(sql_code, args)
        con.commit()
    con.close()


def delete_private_message(recipient, ID):
    con = sqlite3.connect('sunseek.db')
    cur = con.cursor()

    sql_code = ('''DELETE FROM Private_Messages WHERE Recipient = ? AND ID = ?;''')
    args = (recipient, ID,)
    cur.execute(sql_code, args)
    con.commit()
    con.close()


def save_ticker(username, room, ticker):
    con = sqlite3.connect('sunseek.db')
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


def ban_ips(ips):
    con = sqlite3.connect('sunseek.db')
    cur = con.cursor()
    for ip in ips:
        sql_code = ('''INSERT INTO Banned_IPs(IP)
                    VALUES(?);''')
        args = (ip,)
        cur.execute(sql_code, args)
    con.commit()
    con.close()


def unban_ips(ips):
    con = sqlite3.connect('sunseek.db')
    cur = con.cursor()
    for ip in ips:
        sql_code = ('''DELETE FROM Banned_IPs WHERE IP = ?;''')
        args = (ip,)
        cur.execute(sql_code, args)
    con.commit()
    con.close()


def is_ip_banned(ip):
    con = sqlite3.connect('sunseek.db')
    cur = con.cursor()
    sql_code = ('''SELECT * FROM Banned_IPs WHERE IP = ?;''')
    args = (ip,)
    cur.execute(sql_code, args)
    search_result = cur.fetchone()
    con.close()

    if search_result == None:
        return False
    else:
        return True


def ban_users(usernames):
    con = sqlite3.connect('sunseek.db')
    cur = con.cursor()
    for username in usernames:
        sql_code = ('''UPDATE Users
                    SET Banned = ?
                    WHERE Username = ?;''')
        args = (1, username,)
        cur.execute(sql_code, args)
    con.commit()
    con.close()


def unban_users(usernames):
    con = sqlite3.connect('sunseek.db')
    cur = con.cursor()
    for username in usernames:
        sql_code = ('''UPDATE Users
                    SET Banned = ?
                    WHERE Username = ?;''')
        args = (0, username,)
        cur.execute(sql_code, args)
    con.commit()
    con.close()


def ban_room_names(names):
    con = sqlite3.connect('sunseek.db')
    cur = con.cursor()
    for name in names:
        sql_code = ('''INSERT INTO Banned_Room_Names(Room)
                    VALUES(?);''')
        args = (name,)
        cur.execute(sql_code, args)
    con.commit()
    con.close()


def unban_room_names(names):
    con = sqlite3.connect('sunseek.db')
    cur = con.cursor()
    for name in names:
        sql_code = ('''DELETE FROM Banned_Room_Names WHERE Room = ?;''')
        args = (name,)
        cur.execute(sql_code, args)
    con.commit()
    con.close()


def is_room_name_banned(name):
    con = sqlite3.connect('sunseek.db')
    cur = con.cursor()
    sql_code = ('''SELECT * FROM Banned_Room_Names WHERE Room = ?;''')
    args = (name,)
    cur.execute(sql_code, args)
    search_result = cur.fetchone()
    con.close()

    if search_result == None:
        return False
    else:
        return True


def give_privilege(username, time):
    con = sqlite3.connect('sunseek.db')
    cur = con.cursor()
    sql_code = ('''UPDATE Users
                SET Privileged = Privileged + ?
                WHERE Username = ?;''')
    args = (time, username,)
    cur.execute(sql_code, args)
    con.commit()
    con.close()


def gift_privilege(sender_username, username, time):
    con = sqlite3.connect('sunseek.db')
    cur = con.cursor()
    sql_code = ('''SELECT * FROM Users WHERE Username = ?;''')
    args = (sender_username,)
    cur.execute(sql_code, args)
    search_result = cur.fetchone()
    if search_result[3] > time:
        sql_code = ('''UPDATE Users
                    SET Privileged = Privileged + ?
                    WHERE Username = ?;''')
        args = (time, username,)
        cur.execute(sql_code, args)
        sql_code = ('''UPDATE Users
                    SET Privileged = Privileged - ?
                    WHERE Username = ?;''')
        args = (time, sender_username,)
        cur.execute(sql_code, args)


def update_privilege():
    con = sqlite3.connect('sunseek.db')
    cur = con.cursor()
    sql_code = ('''UPDATE Users
                SET Privileged = Privileged - 3600
                WHERE Privileged > 3600;''')
    cur.execute(sql_code)
    sql_code = ('''UPDATE Users
                SET Privileged = 0
                WHERE Privileged < 3600;''')
    cur.execute(sql_code)
    con.commit()

    sql_code = ('''SELECT Username FROM Users WHERE Privileged > 0;''')
    cur.execute(sql_code)
    search_result = cur.fetchall()
    con.close()

    return search_result
