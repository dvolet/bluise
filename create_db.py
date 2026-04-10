import sqlite3

# Connect to (or create) the database file
conn = sqlite3.connect('eloc.db')
c = conn.cursor()

# Create a table for users
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')

conn.commit()
conn.close()
print("Database and 'users' table created successfully!")