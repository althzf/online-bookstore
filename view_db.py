import sqlite3

conn = sqlite3.connect("bookstore.db")
cursor = conn.cursor()

for table in ["users", "books", "orders", "order_items"]:
    print(f"\nTABLE: {table}")
    rows = cursor.execute(f"SELECT * FROM {table}").fetchall()
    for r in rows:
        print(r)

conn.close()
