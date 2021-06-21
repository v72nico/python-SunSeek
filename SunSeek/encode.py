from hashlib import md5
from struct import pack
from socket import inet_aton

def pack_int(item):
    return pack('<I', item)


def pack_str(item):
    encoded_item = item.encode('utf-8')
    length = pack('<I', len(encoded_item))
    return length + encoded_item


def pack_bool(item):
    if item == False:
        bytes_item = b'\x00'
    if item == True:
        bytes_item = b'\x01'
    return bytes_item


def pack_int_64(item):
    return pack('<Q', item)


def pack_int_8(item):
    return pack('<B', item)


def pack_hash(item):
    encoded_item = md5(item.encode('utf-8')).digest()
    length = pack('<I', len(encoded_item))
    return length + encoded_item


def pack_str_lst(items):
    buf = b''
    for item in items:
        buf += pack_str(item)
    return buf


def pack_int_lst(items):
    buf = b''
    for item in items:
        buf += pack_int(item)
    return buf


def pack_possible_parents_lst(parents, ips, ports):
    buf = b''
    for parent, ip, port in zip(parents, ips, ports):
        buf += pack_str(parent)
        buf += inet_aton(ip)
        buf += pack_int(port)
    return buf


def pack_user_data_lst(avgspeed_lst, uploadnum_lst, files_lst, dirs_lst):
    buf = b''
    for avgspeed, uploadnum, files, dirs in zip(avgspeed_lst, uploadnum_lst, files_lst, dirs_lst):
        buf += pack_int(avgspeed)
        buf += pack_int_64(uploadnum)
        buf += pack_int(files)
        buf += pack_int(dirs)
    return buf


def pack_ticker_lst(username_lst, ticker_lst):
    buf = b''
    for username, ticker in zip(username_lst, ticker_lst):
        buf += pack_str(username)
        buf += pack_str(ticker)
    return buf


def pack_ip(ip):
    # IP with little endian is wierd so I have to reverse the octet
    packed_ip_big_endian = inet_aton(ip)
    return packed_ip_big_endian[::-1]


def encode_data(msg_code, *args):
    """Encodes data to be sent to users based on message code."""

    buf = pack_int(msg_code)

    for arg in args:
        if type(arg) == str:
            buf += pack_str(arg)
        if type(arg) == int:
            buf += pack_int(arg)
        if type(arg) == list:
            if arg[0] == '64':
                buf += pack_int_64(arg[1])
            if arg[0] == '8':
                buf += pack_int_64(arg[1])
            if arg[0] == 'ip':
                buf += pack_ip(arg[1])
            if arg[0] == 'hash':
                buf += pack_hash(arg[1])
            if arg[0] == 'str_lst':
                buf += pack_str_lst(arg[1])
            if arg[0] == 'int_lst':
                buf += pack_int_lst(arg[1])
            if arg[0] ==  'possible_parents_lst':
                buf += pack_possible_parents_lst(arg[1], arg[2], arg[3])
            if arg[0] == 'user_data_lst':
                buf += pack_user_data_lst(arg[1], arg[2], arg[3], arg[4])
            if arg[0] == 'ticker_lst':
                buf += pack_ticker_lst(arg[1], arg[2])
        if type(arg) == bool:
            buf += pack_bool(arg)

    # add message length to the begining
    msg_len = pack_int(len(buf))
    complete_msg = msg_len + buf

    return complete_msg
