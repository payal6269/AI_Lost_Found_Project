import sqlite3

# Connect to database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Check if image_data column exists
cursor.execute("PRAGMA table_info(items)")
columns = [column[1] for column in cursor.fetchall()]

if 'image_data' not in columns:
    print("Adding image_data column...")
    cursor.execute("ALTER TABLE items ADD COLUMN image_data TEXT")
    conn.commit()
    print("Column added successfully!")
else:
    print("image_data column already exists")

# Clear old data with file-based images
cursor.execute("UPDATE items SET image_data = '' WHERE image_data IS NULL")
conn.commit()

print("\nCurrent items in database:")
cursor.execute("SELECT id, name, type FROM items")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Name: {row[1]}, Type: {row[2]}")

conn.close()
print("\nDatabase migration complete!")
