import sqlite3
conn = sqlite3.connect('database.db')
conn.execute('DROP TABLE IF EXISTS users')
conn.execute('''CREATE TABLE users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    roll_no TEXT UNIQUE NOT NULL,
    role TEXT DEFAULT "user"
)''')
conn.commit()
conn.close()
print('Users table fixed!')
