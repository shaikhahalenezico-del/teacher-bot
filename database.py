import sqlite3
import os
from datetime import datetime

DB_NAME = os.environ.get('DB_PATH', '/tmp/teacher_bot.db')

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                language TEXT DEFAULT 'ar',
                generations_count INTEGER DEFAULT 0,
                is_subscribed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

def get_user(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return cursor.fetchone()

def create_user(user_id, username):
    if not get_user(user_id):
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
            conn.commit()

def update_language(user_id, language):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (language, user_id))
        conn.commit()

def increment_generation(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET generations_count = generations_count + 1 WHERE user_id = ?", (user_id,))
        conn.commit()

def subscribe_user(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_subscribed = 1 WHERE user_id = ?", (user_id,))
        conn.commit()

def check_access(user_id):
    user = get_user(user_id)
    if not user:
        return False, "User not found"
    
    # user[3] is generations_count, user[4] is is_subscribed
    generations_count = user[3]
    is_subscribed = user[4]
    
    if is_subscribed:
        return True, "Subscribed"
    elif generations_count < 3:
        return True, f"Free trial ({3 - generations_count} left)"
    else:
        return False, "Trial ended"

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
