import sqlite3

with open("schema.sql") as f:
    schema = f.read()

conn = sqlite3.connect("bookstore.db")
conn.executescript(schema)
conn.commit()
conn.close()

print("Database created successfully!")
