import sqlite3


def init_db():

    conn = sqlite3.connect("expense.db")
    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT,
        password TEXT NOT NULL
    )
    """)

    # Add email column if old database does not have it
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
    except sqlite3.OperationalError:
        pass

    # EXPENSES TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        category TEXT,
        amount REAL,
        description TEXT
    )
    """)

    # CATEGORIES TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    """)

    conn.commit()
    conn.close()