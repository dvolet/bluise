import sqlite3
from flask import current_app


def get_connection():
    """
    Create and return a connection to the portfolio database.
    """

    connection = sqlite3.connect(
        current_app.config["DATABASE_PATH"]
    )

    connection.row_factory = sqlite3.Row

    return connection


def create_tables():
    """
    Create the initial portfolio database tables.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            image TEXT,
            technologies TEXT,
            status TEXT DEFAULT 'In Development',
            live_url TEXT,
            github_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()