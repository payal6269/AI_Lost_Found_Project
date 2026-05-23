import sqlite3

conn = sqlite3.connect("database.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS items(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
description TEXT,
type TEXT,
image TEXT
)
""")

conn.commit()
conn.close()

print("Table created successfully")