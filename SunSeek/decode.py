from struct import unpack, error


class Decode_Data():
    def __init__(self, data):
        """Decodes data based on the message code.

        The function intially unpacks the message length and code. Depending
        on the message code the rest of the information in the message is unpacked
        and divided into varius variables.
        """
        self.data = data
        self.offset = 0

        self.dispatch()

    def dispatch(self):
        self.msg_len, self.msg_code = unpack('<II', self.data[:8])
        self.offset = 8
        dispatcher = {
                    '1': self.d_login,
                    '2': self.d_set_listen_port,
                    '3': self.d_username_generic,
                    '5': self.d_username_generic,
                    '6': self.d_username_generic,
                    '7': self.d_username_generic,
                    '13': self.d_say_chatroom,
                    '14': self.d_join_room,
                    '15': self.d_room_generic,
                    '18': self.d_connect_to_peer,
                    '22': self.d_message_user,
                    '23': self.d_message_acked,
                    '26': self.d_file_search,
                    '28': self.d_set_status,
                    '32': self.d_no_data_generic,
                    '33': self.d_no_data_generic,
                    '34': self.d_no_data_generic,
                    '35': self.d_shared_folders_files,
                    '36': self.d_username_generic,
                    '42': self.d_user_search,
                    '51': self.d_item_generic,
                    '52': self.d_item_generic,
                    '54': self.d_no_data_generic,
                    '56': self.d_no_data_generic,
                    '57': self.d_username_generic,
                    '58': self.d_admin_command,
                    '60': self.d_no_data_generic,
                    '63': self.d_no_data_generic,
                    '64': self.d_no_data_generic,
                    '65': self.d_no_data_generic,
                    '67': self.d_no_data_generic,
                    '68': self.d_no_data_generic,
                    '71': self.d_have_no_parent,
                    '73': self.d_no_data_generic,
                    '92': self.d_no_data_generic,
                    '100': self.d_accept_children,
                    '103': self.d_wishlist_search,
                    '110': self.d_no_data_generic,
                    '111': self.d_item_generic,
                    '112': self.d_item_generic,
                    '116': self.d_room_ticker_set,
                    '117': self.d_item_generic,
                    '118': self.d_item_generic,
                    '120': self.d_room_search,
                    '121': self.d_send_upload_speed,
                    '122': self.d_no_data_generic,
                    '123': self.d_give_privileges,
                    '124': self.d_no_data_generic,
                    '125': self.d_no_data_generic,
                    '126': self.d_branch_level,
                    '127': self.d_branch_root,
                    '129': self.d_child_depth,
                    '134': self.d_private_room_add_or_remove_user,
                    '135': self.d_private_room_add_or_remove_user,
                    '136': self.d_room_generic,
                    '137': self.d_room_generic,
                    '138': self.d_room_generic,
                    '141': self.d_private_room_toggle,
                    '142': self.d_change_password,
                    '143': self.d_private_room_add_or_remove_operator,
                    '144': self.d_private_room_add_or_remove_operator,
                    '149': self.d_message_users,
                    '150': self.d_no_data_generic,
                    '151': self.d_no_data_generic,
                    '1001': self.d_cant_connect_to_peer
        }
        dispatcher[str(self.msg_code)]()

    def unpack_str(self):
        length = unpack('<I', self.data[self.offset:4+self.offset])[0]
        self.offset += 4
        item = unpack(f'<{length}s', self.data[self.offset:self.offset+length])[0]
        self.offset += length

        return item.decode('utf-8')

    def unpack_int(self):
        item = unpack('<I', self.data[self.offset:4+self.offset])[0]
        self.offset += 4

        return item

    def unpack_bool(self):
        item = unpack('<c', self.data[self.offset:self.offset+1])[0]
        self.offset += 1
        if item == b'\x01':
            item = True
        if item == b'\x00':
            item = False

        return item

    def d_login(self):
        self.username = self.unpack_str()
        self.password = self.unpack_str()
        self.version = self.unpack_int()
        self.msg_hash = self.unpack_str()

    def d_set_listen_port(self):
        self.port = self.unpack_int()
        if len(self.data) > 12:
            self.use_obfuscation = self.unpack_bool()
            self.obfuscated_port = self.unpack_int()

    def d_username_generic(self):
        self.username = self.unpack_str()

    def d_say_chatroom(self):
        self.room = self.unpack_str()
        self.message = self.unpack_str()

    def d_join_room(self):
        self.room = self.unpack_str()
        try:
            self.private = self.unpack_bool()
        # error refering to struct error
        except error:
            pass

    def d_room_generic(self):
        self.room = self.unpack_str()

    def d_connect_to_peer(self):
         self.token = self.unpack_int()
         self.username = self.unpack_str()
         self.connection_type = self.unpack_str()

    def d_set_status(self):
        self.status = self.unpack_int()

    def d_shared_folders_files(self):
        self.dirs = self.unpack_int()
        self.files = self.unpack_int()

    def d_user_search(self):
        self.username = self.unpack_str()
        self.ticket = self.unpack_int()
        self.query = self.unpack_str()

    def d_no_data_generic(self):
        pass

    def d_message_user(self):
        self.username = self.unpack_str()
        self.message = self.unpack_str()

    def d_message_acked(self):
        self.ID = self.unpack_int()

    def d_file_search(self):
        self.ticket = self.unpack_int()
        self.query = self.unpack_str()

    def d_item_generic(self):
        self.item = self.unpack_str()

    def d_admin_command(self):
        self.password = self.unpack_str()
        str_number = self.unpack_int()
        self.cmd_list = []
        for i in range(0,str_number):
            self.cmd_list.append(self.unpack_str())

    def d_have_no_parent(self):
        self.have_parents = self.unpack_bool()

    def d_accept_children(self):
        self.accept_children = self.unpack_bool()

    def d_wishlist_search(self):
        self.ticket = self.unpack_int()
        self.query = self.unpack_str()

    def d_room_ticker_set(self):
        self.room = self.unpack_str()
        self.ticker = self.unpack_str()

    def d_room_search(self):
        self.room = self.unpack_str()
        self.ticket = self.unpack_int()
        self.query = self.unpack_str()

    def d_send_upload_speed(self):
        self.speed = self.unpack_int()

    def d_give_privileges(self):
        self.username = self.unpack_str()
        self.days = self.unpack_int()

    def d_branch_level(self):
        self.branch_level = self.unpack_int()

    def d_branch_root(self):
        self.branch_root = self.unpack_str()

    def d_child_depth(self):
        self.child_depth = self.unpack_int()

    def d_private_room_add_or_remove_user(self):
        self.room = self.unpack_str()
        self.username = self.unpack_str()

    def d_private_room_toggle(self):
        self.private_toggle = self.unpack_bool()

    def d_change_password(self):
        self.password = self.unpack_str()

    def d_private_room_add_or_remove_operator(self):
        self.room = self.unpack_str()
        self.operator = self.unpack_str()

    def d_message_users(self):
        self.number_of_users = self.unpack_int()
        self.username_lst = []
        for i in range(0, len(self.number_of_users)):
            self.username_lst.append(self.unpack_str())
        self.message = self.unpack_str()

    def d_cant_connect_to_peer(self):
        self.token = self.unpack_int()
        self.username = self.unpack_str()


def parse_data(data, max_msg_size):
    """Seperates messages using message length into each message and calls
     decode_data function.

     Seperates up to 50 messages.
     """

    msgs = []
    msg_len_start = 0
    msg_len = 0
    max_parsed_msgs = 50
    for i in range(0, max_parsed_msgs):
        try:
            msg_len = unpack('<I', data[msg_len_start:msg_len_start+4])[0]
            msg_len += 4
            msgs.append(data[msg_len_start:msg_len+msg_len_start])
            msg_len_start = msg_len+msg_len_start
        except Exception:
            break

    decoded_msgs = []
    for msg in msgs:
        if len(msg) < max_msg_size:
            try:
                decoded_msg = Decode_Data(msg)
                decoded_msgs.append(decoded_msg)
            except Exception as e:
                print('Error on msg decoding', e)
                print(msg)

    return decoded_msgs
