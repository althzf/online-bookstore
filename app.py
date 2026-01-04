from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"


def get_db():
    return sqlite3.connect("bookstore.db")



@app.route("/")
def index():
    db = get_db()
    books = db.execute("SELECT * FROM books").fetchall()
    db.close()
    return render_template("index.html", books=books)



@app.route("/search")
def search():
    q = request.args.get("q", "")
    db = get_db()
    books = db.execute(
        "SELECT * FROM books WHERE title LIKE ? OR author LIKE ?",
        (f"%{q}%", f"%{q}%"),
    ).fetchall()
    db.close()
    return render_template("index.html", books=books, q=q)



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        db = get_db()
        db.execute(
            "INSERT INTO users(name, email, password, role) VALUES (?,?,?, 'user')",
            (name, email, password),
        )
        db.commit()
        db.close()

        flash("Account created! Please log in.")
        return redirect("/login")

    return render_template("register.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE email=?", (email,)
        ).fetchone()
        db.close()

        if user and check_password_hash(user[3], password):
            session["user_id"] = user[0]
            session["name"] = user[1]
            session["role"] = user[4]

            if user[4] == "admin":
                return redirect("/admin")
            return redirect("/")

        flash("Invalid credentials.")

    return render_template("login.html")



@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")



@app.route("/add_to_cart/<int:book_id>")
def add_to_cart(book_id):
    cart = session.get("cart", {})
    cart[str(book_id)] = cart.get(str(book_id), 0) + 1
    session["cart"] = cart
    return redirect("/cart")


@app.route("/cart")
def cart():
    cart = session.get("cart", {})
    db = get_db()
    items = []
    total = 0

    for book_id, qty in cart.items():
        book = db.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
        if book:
            total += book[3] * qty
            items.append((book, qty))

    db.close()
    return render_template("cart.html", items=items, total=total)


@app.route("/cart/remove/<int:book_id>")
def remove_one(book_id):
    cart = session.get("cart", {})
    key = str(book_id)

    if key in cart:
        cart[key] -= 1
        if cart[key] <= 0:
            cart.pop(key)

    session["cart"] = cart
    return redirect("/cart")



@app.route("/cart/delete/<int:book_id>")
def delete_item(book_id):
    cart = session.get("cart", {})
    cart.pop(str(book_id), None)
    session["cart"] = cart
    return redirect("/cart")



@app.route("/checkout", methods=["POST"])
def checkout():
    name = request.form["name"]
    email = request.form["email"]
    cart = session.get("cart", {})

    db = get_db()

    
    user_id = session.get("user_id")

    if not user_id:
        
        existing = db.execute(
            "SELECT id FROM users WHERE email=?",
            (email,)
        ).fetchone()

        if existing:
            user_id = existing[0]
        else:
            
            db.execute(
                "INSERT INTO users(name, email, password, role) VALUES (?,?,?, 'user')",
                (name, email, generate_password_hash("temp")),
            )
            user_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

    
    total = 0
    for book_id, qty in cart.items():
        price = db.execute(
            "SELECT price FROM books WHERE id=?", (book_id,)
        ).fetchone()[0]
        total += price * qty

    
    db.execute("INSERT INTO orders(user_id, total) VALUES (?, ?)", (user_id, total))
    order_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

    
    for book_id, qty in cart.items():
        db.execute(
            "INSERT INTO order_items(order_id, book_id, quantity) VALUES (?,?,?)",
            (order_id, book_id, qty),
        )
        db.execute("UPDATE books SET stock = stock - ? WHERE id=?", (qty, book_id))

    db.commit()
    db.close()

    session["cart"] = {}
    return render_template("success.html")



@app.route("/admin")
def admin_home():
    if session.get("role") != "admin":
        return "Access denied"
    db = get_db()
    books = db.execute("SELECT * FROM books").fetchall()
    db.close()
    return render_template("admin.html", books=books)


@app.route("/admin/add", methods=["GET", "POST"])
def add_book():
    if session.get("role") != "admin":
        return "Access denied"

    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        price = request.form["price"]
        stock = request.form["stock"]

        db = get_db()
        db.execute(
            "INSERT INTO books(title, author, price, stock) VALUES (?,?,?,?)",
            (title, author, float(price), int(stock)),
        )
        db.commit()
        db.close()
        return redirect("/admin")

    return render_template("add_book.html")



@app.route("/admin/orders")
def admin_orders():
    if session.get("role") != "admin":
        return "Access denied"

    db = get_db()

 
    orders = db.execute("""
        SELECT orders.id, users.name, users.email, orders.total, orders.created_at
        FROM orders
        LEFT JOIN users ON users.id = orders.user_id
        ORDER BY orders.id DESC
    """).fetchall()

   
    order_details = {}

    for o in orders:
        order_id = o[0]

        items = db.execute("""
            SELECT books.title, order_items.quantity
            FROM order_items
            JOIN books ON books.id = order_items.book_id
            WHERE order_items.order_id = ?
        """, (order_id,)).fetchall()

        order_details[order_id] = items

    db.close()

    return render_template("admin_orders.html", orders=orders, order_details=order_details)


if __name__ == "__main__":
    app.run(debug=True)
