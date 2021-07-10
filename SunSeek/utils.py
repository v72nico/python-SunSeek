from random import getrandbits, sample
from time import time
import socket


def rand_int():
    return getrandbits(32)


def get_time():
    return int(time())


def days_to_secs(days):
    secs = days * 86400
    return secs


def get_random_lst_items(number, original_lst):
    if len(original_lst) < number:
        number = len(original_lst)
    return sample(original_lst, number)

def is_user_connectable(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    try:
        sock.connect((ip, port))
        connectable = True
    except socket.timeout or ConnectionRefusedError:
        connectable = False
    sock.close()
    return connectable
