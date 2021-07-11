from sys import argv
import socket
from encode import encode_data

if __name__ == "__main__":
    port = int(input('Server Port:'))
    ip = input('Server IP (127.0.0.1 for local machine):')
    admin_password = input('Admin Password:')

    send_msg = encode_data(58, admin_password, len(argv[1:]), ['str_lst', argv[1:]])

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    sock.connect((ip, port))
    sock.send(send_msg)
    sock.close()
