from flask import Flask, render_template, request
import sqlite3
from database import init_db

app = Flask(__name__)

# Create database and tables
init_db()

@app.route("/")
def home():
    return render_template("register.html")


@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]

    conn = sqlite3.connect("expense.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users(username, password) VALUES(?, ?)",
            (username, password)
        )
        conn.commit()
        message = "Registration Successful!"
    except sqlite3.IntegrityError:
        message = "Username already exists!"

    conn.close()

    return render_template("register.html", message=message)


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]

    conn = sqlite3.connect("expense.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    )

    user = cursor.fetchone()

    if user:
        cursor.execute("SELECT * FROM expenses")
        expenses = cursor.fetchall()

        cursor.execute("SELECT SUM(amount) FROM expenses")
        total = cursor.fetchone()[0]

        if total is None:
            total = 0

        conn.close()

        return render_template("dashboard.html", expenses=expenses, total=total)

    conn.close()

    return render_template(
        "login.html",
        message="Invalid Username or Password"
    )

@app.route("/add_expense", methods=["POST"])
def add_expense():

    date = request.form["date"]
    category = request.form["category"]
    amount = request.form["amount"]
    description = request.form["description"]

    conn = sqlite3.connect("expense.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO expenses(date, category, amount, description)
        VALUES(?,?,?,?)
        """,
        (date, category, amount, description)
    )

    conn.commit()

# Get all expenses
    cursor.execute("SELECT * FROM expenses")
    expenses = cursor.fetchall()

# Calculate total
    cursor.execute("SELECT SUM(amount) FROM expenses")
    total = cursor.fetchone()[0]

    if total is None:
        total = 0

    conn.close()

    return render_template(
    "dashboard.html",
    expenses=expenses,
    total=total
)

@app.route("/delete/<int:id>")
def delete(id):

    conn = sqlite3.connect("expense.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM expenses WHERE id=?", (id,))
    conn.commit()

    # Get all expenses
    cursor.execute("SELECT * FROM expenses")
    expenses = cursor.fetchall()

    # Get total amount
    cursor.execute("SELECT SUM(amount) FROM expenses")
    total = cursor.fetchone()[0]

    if total is None:
        total = 0

    conn.close()

    return render_template(
        "dashboard.html",
        expenses=expenses,
        total=total
    )

@app.route("/edit/<int:id>")
def edit(id):

    conn = sqlite3.connect("expense.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM expenses WHERE id=?", (id,))

    expense = cursor.fetchone()

    conn.close()

    return render_template("edit_expense.html", expense=expense)

@app.route("/update/<int:id>", methods=["POST"])
def update(id):

    date = request.form["date"]
    category = request.form["category"]
    amount = request.form["amount"]
    description = request.form["description"]

    conn = sqlite3.connect("expense.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE expenses
        SET date=?, category=?, amount=?, description=?
        WHERE id=?
    """, (date, category, amount, description, id))

    conn.commit()

    # Get all expenses
    cursor.execute("SELECT * FROM expenses")
    expenses = cursor.fetchall()

    # Calculate total expense
    cursor.execute("SELECT SUM(amount) FROM expenses")
    total = cursor.fetchone()[0]

    if total is None:
        total = 0

    conn.close()

    return render_template(
        "dashboard.html",
        expenses=expenses,
        total=total
    )

@app.route("/search", methods=["POST"])
def search():

    category = request.form["category"]

    conn = sqlite3.connect("expense.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM expenses WHERE category LIKE ?",
        ('%' + category + '%',)
    )

    expenses = cursor.fetchall()

    cursor.execute("SELECT SUM(amount) FROM expenses")
    total = cursor.fetchone()[0]

    if total is None:
        total = 0

    conn.close()

    return render_template(
        "dashboard.html",
        expenses=expenses,
        total=total
    )

if __name__ == "__main__":
    app.run(debug=True)