import sqlite3
from werkzeug.security import generate_password_hash

name = "Admin"
email = "admin@store.com"
password = "admin123"   # you can change this

conn = sqlite3.connect("bookstore.db")
cursor = conn.cursor()

cursor.execute("""
INSERT INTO users (name, email, password, role)
VALUES (?, ?, ?, 'admin')
""", (name, email, generate_password_hash(password)))

conn.commit()
conn.close()

print("Admin created successfully!")
