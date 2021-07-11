# SunSeek
This is an alternative server software using the soulseek protocol. Most core features work (private rooms are buggy). Not tested at scale. Not production ready.

To run server, first run make_db.py to create databases, then run the run.py.

Admin commands can be run through admin.py.

List of commands:
- Ban_IPs
- Unban_IPs
- Ban_Users
- Unban_Users
- Delete_Rooms
- Ban_Room_Names
- Unban_Room_Names
- Add_User
- Give_Privilege

Examples:
- python3 admin.py Ban_IPs 0.0.0.0 1.1.1.1
- python3 admin.py Ban_Users EvilUser


In the config file config.ini various server settings can be changed. If a server is private users cannot join unless an account is created for them with the admin command Add_User.

- ✅ Search users files
- ✅ PM users
- ✅ Public Chat rooms
- ✅ View User Info
- ✅ Server Settings
- ✅ Admin Commands
- ✅ Admin CLI Interface
- ❌ Private Chat rooms
- ❌ Protection from abusive users
- ❌ Recommendations
