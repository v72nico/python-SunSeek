from random import getrandbits, sample
from time import time
import json
from urllib.request import urlopen
import socket
import linecache
import sys

def get_country(ip):
    try:
        with urlopen(f"https://ipapi.co/{ip}/json/") as url:
            data = json.loads(url.read().decode())
            print(data['country_code'])
            return data['country_code']
    except Exception:
        return 'ZZ'


def rand_int():
    return getrandbits(32)


def get_time():
    return int(time())


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
