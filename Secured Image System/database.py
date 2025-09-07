import sqlite3
from config import DATABASE_NAME

def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # 🆕 Create uploads table with category column
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            filename TEXT NOT NULL,
            category TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")
