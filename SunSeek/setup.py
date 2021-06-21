from db import create_chat_db, create_users_db
from config import create_config


if __name__ == "__main__":
    create_users_db()
    create_chat_db()
    create_config()
