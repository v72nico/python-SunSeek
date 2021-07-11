from twisted.internet.protocol import Factory, Protocol
from twisted.internet.task import LoopingCall
from twisted.internet.threads import deferToThread

from db import login_user, user_exist, save_private_message, get_saved_private_messages, delete_private_message, ban_ips, unban_ips, is_ip_banned, ban_users, unban_users, \
ban_room_names, unban_room_names, is_room_name_banned, give_privilege, update_privilege, change_password_db
from decode import parse_data
from encode import encode_data
from utils import get_time, rand_int, get_random_lst_items, is_user_connectable, days_to_secs
from rooms import Chatroom
from config import get_port, get_config_data


class slskProtocol(Protocol):
    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.peer = self.transport.getPeer()
        self.ip = self.peer.host
        if is_ip_banned(self.ip):
            self.transport.loseConnection()

        self.username = 'null'
        self.logged_in = False
        self.port = 2234  # default listening port
        self.use_obfuscation = False
        self.obfuscated_port = 2235
        self.privileged = False
        self.added_me = []
        self.added_users = []
        self.status = 0
        self.avgspeed = 0
        self.uploadnum = 0
        self.files = 0
        self.dirs = 0
        self.likes = []
        self.hates = []
        self.joined_rooms = []
        self.have_parents = False
        self.var_accept_children = False
        self.var_branch_level = 0
        self.var_branch_root = None
        self.var_child_depth = 0
        self.private_toggle = False
        self.country = 'ZZ'

    def connectionLost(self, reason):
        # send status update to people who have them added
        self.status = 0
        self.send_status_update()

        # Remove user from factory lists and from room users
        if self.logged_in == True:
            del self.factory.users[self.username]
            print('deleted self', self.factory.users)
        try:
            self.factory.privileged.remove(self.username)
        except ValueError:
            pass
        try:
            self.factory.public_room_users.remove(self.username)
        except ValueError:
            pass
        try:
            self.factory.want_children.remove(self.username)
        except ValueError:
            pass
        try:
            for room in self.joined_rooms:
                self.factory.rooms[room].users.remove(self.username)
                # if room is empty delete it
                if self.factory.rooms[room].users == 0:
                    del self.factory.rooms[room]
                # otherwise tell other users in the room somebody left
                else:
                    send_msg = encode_data(17, room, self.username)
                    for name in self.factory.rooms[room].users:
                        self.factory.users[name].transport.write(send_msg)
        except Exception:
            pass
        try:
            for name in self.added_users:
                self.factory.users[name].added_me.remove(self.username)
        except Exception:
            pass
        try:
            for name in self.added_me:
                self.factory.users[name].added_users.remove(self.username)
        except Exception:
            pass

        print(reason)

    def dataReceived(self, data):
        dispatcher = {
                    '2': self.set_wait_port,
                    '3': self.get_peer_address,
                    '5': self.add_user,
                    '6': self.remove_user,
                    '7': self.get_user_status,
                    '13': self.say_chatroom,
                    '14': self.join_room,
                    '15': self.leave_room,
                    '18': self.connect_to_peer,
                    '22': self.message_user,
                    '23': self.message_acked,
                    '26': self.file_search,
                    '28': self.set_status,
                    '35': self.shared_folders_files,
                    '36': self.get_user_stats,
                    '42': self.user_search,
                    '51': self.add_thing_i_like,
                    '52': self.remove_thing_i_like,
                    '54': self.recommendations,
                    '56': self.global_recommendations,
                    '57': self.user_interests,
                    '58': self.admin_command,
                    '64': self.room_list,
                    '71': self.have_no_parent,
                    '92': self.check_privileges,
                    '100': self.accept_children,
                    '103': self.wishlist_search,
                    '110': self.similar_users,
                    '111': self.item_recommendations,
                    '112': self.item_similar_users,
                    '116': self.room_ticker_set,
                    '117': self.add_thing_i_hate,
                    '118': self.remove_thing_i_hate,
                    '120': self.room_search,
                    '121': self.send_upload_speed,
                    '123': self.give_privileges,
                    '126': self.branch_level,
                    '127': self.branch_root,
                    '129': self.child_depth,
                    '134': self.private_room_add_user,
                    '135': self.private_room_remove_user,
                    '136': self.private_room_dismember,
                    '137': self.private_room_disown,
                    '141': self.private_room_toggle,
                    '142': self.change_password,
                    '143': self.private_room_add_operator,
                    '144': self.private_room_remove_operator,
                    '149': self.message_users,
                    '150': self.join_public_room,
                    '151': self.leave_public_room,
                    '1001': self.cant_connect_to_peer
        }

        msgs = parse_data(data, self.factory.settings['max_msg_size'])
        for msg in msgs:
            print(self.username)
            print(msg.__dict__)

            if msg.msg_code == 1:
                try:
                    self.login(msg)
                except Exception as e:
                    print('Error logging in ', e)

            elif msg.msg_code == 58:
                try:
                    self.admin_command(msg)
                except Exception as e:
                    print('Error in Admin Command ', e)

            elif self.logged_in == True:
                try:
                    dispatcher[str(msg.msg_code)](msg)
                except Exception as e:
                    print(f"Error responding to msg. Msg Code: {msg.msg_code}, Error: ", e)

    def login(self, msg):
        self.username = msg.username
        self.logged_in = False
        # Trying to keep password temporary by not sticking it user data
        password = msg.password
        login_result = login_user(self.username, password, self.factory.settings['private_server'])

        if login_result[0] == 'success':
            # Check if user already logged in and kick if the same user
            if msg.username in self.factory.users:
                user = self.factory.users[msg.username]
                send_msg = encode_data(41)
                user.transport.write(send_msg)
                user.transport.loseConnection()

            # Set privilege
            privilege_status = login_result[1]
            if privilege_status > 0:
                self.privileged = True
                if self.username not in self.factory.privileged:
                    self.factory.privileged.append(self.username)

            self.logged_in = True

            # Add user to user list
            self.factory.users[self.username] = self

            # Start repeating loopingcalls
            LoopingCall(self.possible_parents).start(60)

            send_msg = encode_data(1, True, self.factory.greeting, ['ip', self.ip], ['hash', password])
            self.transport.write(send_msg)

            # Send private messages from when offline
            pms = get_saved_private_messages(self.username)
            for pm in pms:
                send_msg = encode_data(22, pm['ID'], pm['timestamp'], pm['username'], pm['message'], False)
                self.transport.write(send_msg)

            # Send room list
            # Argument None in place of where msg normally is
            self.room_list(None)

            self.privileged_users()

        # TODO Max login attempts
        elif login_result[0] == 'failure':
            reason = login_result[1]
            send_msg = encode_data(1, False, reason)
            self.transport.write(send_msg)

    def set_wait_port(self, msg):
        self.port = msg.port
        try:
            self.use_obfuscation = msg.use_obfuscation
            self.obfuscated_port = msg.obfuscated_port
        except Exception:
            pass

    def get_peer_address(self, msg):
        if msg.username in self.factory.users:
            user = self.factory.users[msg.username]
            send_msg = encode_data(3, user.username, ['ip', user.ip], user.port, user.use_obfuscation, user.obfuscated_port)
            self.transport.write(send_msg)

    def add_user(self, msg):
        # TODO somethings wrong because user should be removed from list at exit
        if msg.username in self.factory.users:
            user = self.factory.users[msg.username]
            send_msg = encode_data(5, user.username, True, user.status, user.avgspeed, ['64', user.uploadnum], user.files, user.dirs, user.country)
            self.transport.write(send_msg)
            if self.username not in user.added_me:
                user.added_me.append(self.username)
            if msg.username not in self.added_users:
                self.added_users.append(msg.username)
        else:
            send_msg = encode_data(5, msg.username, False)
            self.transport.write(send_msg)

    def remove_user(self, msg):
        if msg.username in self.factory.users:
            user = self.factory.users[msg.username]
            if self.username in user.added_me:
                user.added_me.remove(self.username)
            if msg.username in self.added_users:
                self.added_users.remove(msg.username)

    def get_user_status(self, msg):
        if msg.username in self.factory.users:
            user = self.factory.users[msg.username]
            send_msg = encode_data(7, user.username, user.status, user.privileged)
            self.transport.write(send_msg)
        elif user_exist(msg.username):
            send_msg = encode_data(7, msg.username, 0, False)
            self.transport.write(send_msg)

    def say_chatroom(self, msg):
        if msg.room in self.factory.rooms:
            room = self.factory.rooms[msg.room]
            if self.username in room.users:
                send_msg = encode_data(13, msg.room, self.username, msg.message)
                for name in room.users:
                    self.factory.users[name].transport.write(send_msg)

                # send to public chatroom users
                if room.private == False:
                    send_msg = (152, msg.room, self.username, msg.message)
                    for name in self.factory.public_room_users:
                        self.factory.users[name].transport.write(send_msg)

    def join_room(self, msg):
        # If room already exists
        if msg.room in self.factory.rooms:
            room = self.factory.rooms[msg.room]

            if room.private == False:
                if msg.room not in self.joined_rooms:
                    self.joined_rooms.append(msg.room)
                if self.username not in room.users:
                    room.users.append(self.username)

                status_lst, avgspeed_lst, uploadnum_lst, files_lst, dirs_lst, slotsfree_lst, country_lst = self.room_user_stats(room)

                send_msg = encode_data(14, msg.room, len(room.users), ['str_lst', room.users], len(room.users), ['int_lst', status_lst], len(room.users), ['user_data_lst', avgspeed_lst, uploadnum_lst, files_lst, dirs_lst], len(room.users), ['int_lst', slotsfree_lst], len(room.users), ['str_lst', country_lst])
                self.transport.write(send_msg)

                send_msg = encode_data(16, msg.room, self.username, self.status, self.avgspeed, self.uploadnum, self.files, self.dirs, 1, self.country)
                for name in room.users:
                    if name != self.username:
                        self.factory.users[name].transport.write(send_msg)

                username_lst, ticker_lst = self.ticker_state(room)
                send_msg = encode_data(113, msg.room, len(room.tickers), ['ticker_lst', username_lst, ticker_lst])
                self.transport.write(send_msg)

            if room.private == True:
                if self.username in room.allowed_users:
                    if msg.room not in self.joined_rooms:
                        self.joined_rooms.append(msg.room)
                    if self.username not in room.users:
                        room.users.append(self.username)

                    status_lst, avgspeed_lst, uploadnum_lst, files_lst, dirs_lst, slotsfree_lst, country_lst = self.room_user_stats(room)

                    send_msg = encode_data(14, msg.room, len(room.users), ['str_lst', room.users], len(room.users), ['int_lst', status_lst], len(room.users), ['user_data_lst', avgspeed_lst, uploadnum_lst, files_lst, dirs_lst], len(room.users), ['int_lst', slotsfree_lst], len(room.users), ['str_lst', country_lst], room.owner, len(room.operators), ['str_lst', room.operators])
                    self.transport.write(send_msg)

                    send_msg = encode_data(16, msg.room, self.username, self.status, self.avgspeed, self.uploadnum, self.files, self.dirs, 1, self.country)
                    for name in room.users:
                        if name != self.username:
                            self.factory.users[name].transport.write(send_msg)

                    self.send_private_room_update(msg.room)

                    username_lst, ticker_lst = self.ticker_state(room)
                    send_msg = encode_data(113, msg.room, len(room.tickers), ['ticker_lst', username_lst, ticker_lst])
                    self.transport.write(send_msg)

                else:
                    send_msg = encode_data(1003, msg.room)
                    self.transport.write(send_msg)

        # If room dosent exists
        else:
            if not is_room_name_banned(msg.room):
                try:
                    self.factory.rooms[msg.room] = Chatroom(msg.room, msg.private)
                except AttributeError:
                    self.factory.rooms[msg.room] = Chatroom(msg.room, False)
                room = self.factory.rooms[msg.room]
                self.joined_rooms.append(msg.room)
                room.users.append(self.username)
                if room.private == True:
                    room.owner = self.username
                    send_msg = encode_data(14, msg.room, 1, self.username, 1, self.status, 1, self.avgspeed, ['64', self.uploadnum], self.files, self.dirs, 1, 1, 1, self.country, self.username, 0)
                else:
                    send_msg = encode_data(14, msg.room, 1, self.username, 1, self.status, 1, self.avgspeed, ['64', self.uploadnum], self.files, self.dirs, 1, 1, 1, self.country)
                self.transport.write(send_msg)

    def leave_room(self, msg):
        if msg.room in self.factory.rooms:
            room = self.factory.rooms[msg.room]
            room.users.remove(self.username)
            self.joined_rooms.remove(msg.room)

            # if room is empty delete it
            if len(room.users) == 0:
                del self.factory.rooms[msg.room]

            # otherwise tell other users in the room somebody left
            else:
                send_msg = encode_data(17, msg.room, self.username)
                for name in room.users:
                    self.factory.users[name].transport.write(send_msg)

            send_msg = encode_data(15, msg.room)
            self.transport.write(send_msg)

    def connect_to_peer(self, msg):
        if msg.username in self.factory.users:
            user = self.factory.users[msg.username]
            send_msg = encode_data(18, user.username, msg.connection_type, user.ip, user.port, msg.token, user.privileged, user.use_obfuscation, user.obfuscated_port)
            self.transport.write(send_msg)

    def message_user(self, msg):
        if msg.username in self.factory.users:
            user = self.factory.users[msg.username]
            send_msg = encode_data(22, rand_int(), get_time(), self.username, msg.message, True)
            user.transport.write(send_msg)

        # save message for later if offline
        elif user_exist(msg.username):
            save_private_message(msg.message, self.username, msg.username, get_time(), rand_int(), self.factory.settings['max_pms'])

    def message_acked(self, msg):
        # Acknowledge message deletes past offline private messages
        delete_private_message(self.username, msg.ID)

    def file_search(self, msg):
        send_msg = encode_data(26, self.username, msg.ticket, msg.query)
        for user in self.factory.users.values():
            if user != self:
                user.transport.write(send_msg)

    def set_status(self, msg):
        self.status = msg.status
        self.send_status_update()

    def shared_folders_files(self, msg):
        self.dirs = msg.dirs
        self.files = msg.files
        self.send_stats_update()

    def get_user_stats(self, msg):
        if msg.username in self.factory.users:
            user = self.factory.users[msg.username]
            send_msg = encode_data(36, user.username, user.avgspeed, ['64', user.uploadnum], user.files, user.dirs)

    def user_search(self, msg):
        send_msg = encode_data(26, self.username, msg.ticket, msg.query)
        self.factory.users[msg.username].transport.write(send_msg)

    def add_thing_i_like(self, msg):
        self.likes.append(msg.item)

    def remove_thing_i_like(self, msg):
        self.likes.remove(msg.item)

    def recommendations(self, msg):
        # TODO
        pass

    def global_recommendations(self, msg):
        # TODO
        pass

    def user_interests(self, msg):
        if msg.username in self.factory.users:
            user = self.factory.users[msg.username]
            send_msg = encode_data(57, user.username, len(user.likes), ['str_lst', user.likes], len(user.hates), ['str_lst', user.hates])
            self.transport.write(send_msg)

    def admin_command(self, msg):
        if self.factory.settings['admin_password'] != None:
            if msg.password == self.factory.settings['admin_password']:
                if msg.cmd_list[0] == 'Ban_IPs':
                    ban_ips(msg.cmd_list[1:])
                    for user in self.factory.users.values():
                        if user.ip in msg.cmd_list[1:]:
                            user.transport.loseConnection()

                if msg.cmd_list[0] == 'Unban_IPs':
                    unban_ips(msg.cmd_list[1:])

                if msg.cmd_list[0] == 'Ban_Users':
                    ban_users(msg.cmd_list[1:])
                    for name in self.factory.users:
                        if name in msg.cmd_list[1:]:
                            self.factory.users[name].transport.loseConnection()

                if  msg.cmd_list[0] == 'Unban_Users':
                    unban_users(msg.cmd_list[1:])

                if msg.cmd_list[0] == 'Delete_Rooms':
                    for room in self.factory.rooms.values():
                        if room.name in msg.cmd_list[1:]:
                            send_msg = encode_data(15, room.name)
                            for name in room.users:
                                self.factory.users[name].transport.write(send_msg)
                            del self.factory.rooms[room.name]

                if msg.cmd_list[0] == 'Ban_Room_Names':
                    ban_room_names(msg.cmd_list[1:])
                    for room in self.factory.rooms.values():
                        if room.name in msg.cmd_list[1:]:
                            send_msg = encode_data(15, room.name)
                            for name in room.users:
                                self.factory.users[name].transport.write(send_msg)
                            del self.factory.rooms[room.name]

                if msg.cmd_list[0] == 'Unban_Room_Names':
                    unban_room_names(msg.cmd_list[1:])

                if msg.cmd_list[0] == 'Add_User':
                    # 3rd arg False to bypass private server lock
                    login_user(msg.cmd_list[1], msg.cmd_list[2], False)

                if msg.cmd_list[0] == 'Give_Privilege':
                    time = days_to_secs(int(msg.cmd_list[2]))
                    give_privilege(msg.cmd_list[1], time)

    def room_list(self, msg):
        rooms = self.factory.rooms

        number_of_users_public = []
        rooms_public = []

        private_rooms_not_owned = []
        number_of_users_not_owned = []

        private_rooms_operator = []

        private_rooms_owned = []
        number_of_users_owned = []

        for room in rooms.values():
            if room.private == False:
                rooms_public.append(room.name)
                number_of_users_public.append(len(room.users))
            if room.private == True:
                if room.owner == self.username:
                    private_rooms_owned.append(room.name)
                    number_of_users_owned.append(len(room.users))
                else:
                    private_rooms_not_owned.append(room.name)
                    number_of_users_not_owned.append(len(room.users))
                    if self.username in room.operators:
                        private_rooms_operator.append(room.name)

        send_msg = encode_data(64, len(rooms_public), ['str_lst', rooms_public], len(rooms_public), ['int_lst', number_of_users_public], len(private_rooms_owned), ['str_lst', private_rooms_owned], len(private_rooms_owned), ['int_lst', number_of_users_owned], len(private_rooms_not_owned), ['str_lst', private_rooms_not_owned], len(private_rooms_not_owned), ['int_lst', number_of_users_not_owned], len(private_rooms_operator), ['str_lst', private_rooms_operator])
        self.transport.write(send_msg)

    def have_no_parent(self, msg):
        self.have_parents = msg.have_parents

    def check_privileges(self, msg):
        # TODO
        pass

    def accept_children(self, msg):
        self.var_accept_children = msg.accept_children
        if msg.accept_children == False:
            if self.username in self.factory.want_children:
                self.factory.want_children.remove(self.username)
        if msg.accept_children == True:
            if self.username not in self.factory.want_children:
                self.factory.want_children.append(self.username)

    def wishlist_search(self, msg):
        # TODO
        # TODO looping call wishlist interval??
        pass

    def similar_users(self, msg):
        # TODO
        pass

    def item_recommendations(self, msg):
        # TODO
        pass

    def item_similar_users(self, msg):
        # TODO
        pass

    def room_ticker_set(self, msg):
        if msg.room in self.factory.rooms:
            room = self.factory.rooms[msg.room]
            if self.username in room.tickers:
                del self.factory.rooms[msg.room].tickers[self.username]
            if msg.ticker != '':
                room.tickers[self.username] = msg.ticker
                send_msg = encode_data(114, msg.room, self.username, msg.ticker)
                for name in room.users:
                    if name != self.username:
                        self.factory.users[name].transport.write(send_msg)
            if msg.ticker == '':
                send_msg = encode_data(115, msg.room, self.username)
                for name in room.users:
                    if name != self.username:
                        self.factory.users[name].transport.write(send_msg)

            username_lst, ticker_lst = self.ticker_state(room)
            send_msg = encode_data(113, msg.room, len(room.tickers), ['ticker_lst', username_lst, ticker_lst])
            for name in room.users:
                self.factory.users[name].transport.write(send_msg)

    def add_thing_i_hate(self, msg):
        self.hates.append(msg.item)

    def remove_thing_i_hate(self, msg):
        self.hates.remove(msg.item)

    def room_search(self, msg):
        if msg.room in self.factory.rooms:
            room = self.factory.rooms[msg.room]
            send_msg = encode_data(26, self.username, msg.ticket, msg.query)
            for name in room.users:
                if name != self.username:
                    self.factory.users[name].transport.write(send_msg)

    def send_upload_speed(self, msg):
        self.avgspeed = msg.speed
        self.send_stats_update()

    def give_privileges(self, msg):
        if user_exist(msg.username):
            time = days_to_secs(msg.days)
            gift_privilege(self.username, msg.username, time)

    def branch_level(self, msg):
        self.var_branch_level = msg.branch_level

    def branch_root(self, msg):
        self.var_branch_root = msg.branch_root

    def child_depth(self, msg):
        self.var_child_depth = msg.child_depth

    def private_room_add_user(self, msg):
        if msg.room in self.factory.rooms and msg.username in self.factory.users:
            room = self.factory.rooms[msg.room]
            # If your owner or operator
            if self.username == room.owner or self.username in room.operators:
                user = self.factory.users[msg.username]
                if user.private_toggle == True:
                    send_msg = encode_data(139, msg.room)
                    user.transport.write(send_msg)
                    if msg.username not in room.users:
                        room.users.append(msg.username)
                    if msg.room not in user.joined_rooms:
                        user.joined_rooms.append(msg.room)
                    if msg.username not in room.allowed_users:
                        room.allowed_users.append(msg.username)

                    status_lst, avgspeed_lst, uploadnum_lst, files_lst, dirs_lst, slotsfree_lst, country_lst = self.room_user_stats(room)

                    send_msg = encode_data(14, msg.room, len(room.users), ['str_lst', room.users], len(room.users), ['int_lst', status_lst], len(room.users), ['user_data_lst', avgspeed_lst, uploadnum_lst, files_lst, dirs_lst], len(room.users), ['int_lst', slotsfree_lst], len(room.users), ['str_lst', country_lst], room.owner, len(room.operators), ['str_lst', room.operators])
                    user.transport.write(send_msg)

                    send_msg = encode_data(134, msg.room, msg.username)
                    self.transport.write(send_msg)

                    send_msg = encode_data(16, msg.room, user.username, user.status, user.avgspeed, user.uploadnum, user.files, user.dirs, 1, user.country)
                    for name in room.users:
                        if name != msg.username:
                            self.factory.users[name].transport.write(send_msg)

                    self.send_private_room_update(msg.room)

    def private_room_remove_user(self, msg):
        if msg.room in self.factory.rooms and msg.username in self.factory.users:
            room = self.factory.rooms[msg.room]
            # If your owner or operator
            if self.username == room.owner or self.username in room.operators:
                if msg.username != room.owner or msg.username not in room.operators:
                    send_msg = encode_data(140, msg.room)
                    user = self.factory.users[msg.username]
                    user.transport.write(send_msg)

                    if msg.username in room.users:
                        room.users.remove(msg.username)
                    if msg.room in user.joined_rooms:
                        user.joined_rooms.remove(msg.room)
                    if msg.username in room.allowed_users:
                        room.allowed_users.remove(msg.username)

                    send_msg = encode_data(15, msg.room)
                    user.transport.write(send_msg)

                    send_msg = encode_data(135, msg.room, msg.username)
                    self.transport.write(send_msg)

                    send_msg = encode_data(17, msg.room, user.username)
                    for name in room.users:
                        if name != msg.username:
                            self.factory.users[name].transport.write(send_msg)

                    self.send_private_room_update(msg.room)

    def private_room_dismember(self, msg):
        if msg.room in self.factory.rooms:
            room = self.factory.rooms[msg.room]
            room.users.remove(self.username)
            room.allowed_users.remove(self.username)
            if len(room.users) == 0:
                del self.factory.rooms[msg.room]
            else:
                send_msg = encode_data(17, msg.room, self.username)
                for name in room.users:
                    if name != self.username:
                        self.factory.users[name].transport.write(send_msg)

                self.send_private_room_update(msg.room)

            send_msg = encode_data(15, msg.room)
            self.transport.write(send_msg)

    def private_room_disown(self, msg):
        if msg.room in self.factory.rooms:
            room = self.factory.rooms[msg.room]
            if self.username == room.owner:
                if room.operators > 0:
                    room.owner = get_random_lst_items(1, room.operators)
                else:
                    room.owner = get_random_lst_items(1, room.users)

                self.send_private_room_update(msg.room)

    def private_room_toggle(self, msg):
        self.private_toggle = msg.private_toggle
        send_msg = encode_data(141, msg.private_toggle)
        self.transport.write(send_msg)

    def change_password(self, msg):
        change_password_db(self.username, msg.password)
        send_msg = encode_data(142, msg.password)
        self.transport.write(send_msg)

    def private_room_add_operator(self, msg):
        if msg.room in self.factory.rooms and msg.operator in self.factory.users:
            room = self.factory.rooms[msg.room]
            if self.username == room.owner or self.username in room.operators:
                if msg.operator not in room.operators:
                        # Owner cant be operator
                        if room.owner != msg.operator:
                            # send return confirmation msg
                            send_msg = encode_data(143, msg.room, msg.operator)
                            self.transport.write(send_msg)
                            #send msg to new operator
                            send_msg = encode_data(145, msg.room)
                            user = self.factory.users[msg.operator]
                            user.transport.write(send_msg)
                            # add operator to room
                            room.operators.append(msg.operator)

                            self.send_private_room_update(msg.room)

    def private_room_remove_operator(self, msg):
        if msg.room in self.factory.rooms and msg.operator in self.factory.users:
            room = self.factory.rooms[msg.room]
            if self.username == room.owner:
                if msg.operator in room.operators:
                    # send return confirmation msg
                    send_msg = encode_data(144, msg.room, msg.operator)
                    self.transport.write(send_msg)
                    #send msg to removed operator
                    send_msg = encode_data(146, msg.room)
                    user = self.factory.users[msg.operator]
                    user.transport.write(send_msg)
                    # remove operator from room
                    room.operators.remove(msg.operator)

                    self.send_private_room_update(msg.room)

    def message_users(self, msg):
        send_msg = encode_data(22, rand_int(), get_time(), self.username, msg.message, True)
        for name in msg.username_lst:
            if name in self.factory.users:
                self.factory.users[name].transport.write(send_msg)
            elif user_exist(name):
                save_private_message(msg.message, self.username, name, get_time(), rand_int(), self.factory.settings['max_pms'])

    def join_public_room(self, msg):
        if self.username not in self.factory.public_room_users:
            self.factory.public_room_users.append(self.username)

    def leave_public_room(self, msg):
        if self.username in self.factory.public_room_users:
            self.factory.public_room_users.remove(self.username)

    def cant_connect_to_peer(self, msg):
        if msg.username in self.factory.users:
            ip = self.factory.users[msg.username].ip
            port = self.factory.users[msg.username].port
            user_connectable = deferToThread(is_user_connectable, ip, port)
            self_connectable = deferToThread(is_user_connectable, self.ip, self.port)
            if not user_connectable and not self_connectable:
                send_msg = encode_data(1001, msg.token, msg.username)
                self.transport.write(send_msg)

    def privileged_users(self):
        privileged = self.factory.privileged
        send_msg = encode_data(69, len(privileged), ['str_lst', privileged])
        self.transport.write(send_msg)

    def send_stats_update(self):
        for name in self.added_me:
            user = self.factory.users[name]
            send_msg = encode_data(36, self.username, self.avgspeed, ['64', self.uploadnum], self.files, self.dirs)
            user.transport.write(send_msg)

    def send_status_update(self):
        for name in self.added_me:
            user = self.factory.users[name]
            send_msg = encode_data(7, self.username, self.status, self.privileged)
            user.transport.write(send_msg)

    def possible_parents(self):
        if self.have_parents == False:
            var_possible_parents = get_random_lst_items(10, self.factory.want_children)
            ips = []
            ports = []
            for parent in var_possible_parents:
                ips.append(self.factory.users[parent].ip)
                ports.append(self.factory.users[parent].port)
            send_msg = encode_data(102, len(var_possible_parents), ['possible_parents_lst', var_possible_parents, ips, ports])
            self.transport.write(send_msg)

    def send_private_room_update(self, room_name):
        # Message codes 133 and 148
        room = self.factory.rooms[room_name]

        alterable_users = room.users.copy()
        alterable_users.remove(room.owner)
        if self.username != room.owner:
            for operator in room.operators:
                alterable_users.remove(operator)

        send_msg = encode_data(133, room_name, len(room.users), ['str_lst', alterable_users])
        self.factory.users[room.owner].transport.write(send_msg)
        for operator in room.operators:
            self.factory.users[operator].transport.write(send_msg)

        send_msg = encode_data(148, room_name, len(room.operators), ['str_lst', room.operators])
        self.factory.users[room.owner].transport.write(send_msg)

    def room_user_stats(self, room):
        status_lst = []
        avgspeed_lst = []
        uploadnum_lst = []
        files_lst = []
        dirs_lst = []
        slotsfree_lst = []
        country_lst = []

        for name in room.users:
            user = self.factory.users[name]
            status_lst.append(user.status)
            avgspeed_lst.append(user.avgspeed)
            uploadnum_lst.append(user.uploadnum)
            files_lst.append(user.files)
            dirs_lst.append(user.dirs)
            # Slotsfree not implemented
            slotsfree_lst.append(1)
            country_lst.append(user.country)

        return status_lst, avgspeed_lst, uploadnum_lst, files_lst, dirs_lst, slotsfree_lst, country_lst

    def ticker_state(self, room):
        username_lst = room.tickers.keys()
        ticker_lst = room.tickers.values()

        return username_lst, ticker_lst


class slskFactory(Factory):
    """Factory for slsk_Protocol users"""
    def __init__(self):
        self.users = {}
        self.rooms = {}
        self.privileged = []
        self.public_room_users = []
        self.want_children = []

        self.settings = get_config_data()
        self.greeting = self.settings['greeting']

        #LoopingCall(self.manage_privileges).start(3600, False)

    def buildProtocol(self, addr):
        if len(self.users) < self.settings['max_users']:
            return slskProtocol(self)

    def manage_privileges(self):
        # looping call to check and update privilleges, and privilege list, and update time remaining in database
        # send upate of msg code 69
        # TODO broken
        self.privileged = update_privilege()
        privileged = self.privileged
        send_msg = encode_data(69, len(privileged), ['str_lst', privileged])
        for user in self.users.values():
            user.transport.write(send_msg)
