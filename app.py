from flask import Flask, render_template, request, redirect, session
import sqlite3
from database import init_db

app = Flask(__name__)

app.secret_key = "expense_tracker_secret_key"

init_db()


def get_db():
    conn = sqlite3.connect("expense.db")
    return conn


@app.route("/")
def home():
    return render_template("register.html")


# =========================
# REGISTER
# =========================

@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not username or not password:
        return render_template(
            "register.html",
            message="Username and password are required."
        )

    if confirm_password and password != confirm_password:
        return render_template(
            "register.html",
            message="Passwords do not match."
        )

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO users(username, email, password)
            VALUES(?,?,?)
            """,
            (username, email, password)
        )

        conn.commit()
        conn.close()

        return render_template(
            "login.html",
            message="Registration successful! Please login."
        )

    except sqlite3.IntegrityError:
        conn.close()

        return render_template(
            "register.html",
            message="Username already exists!"
        )


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, username, email
        FROM users
        WHERE username=? AND password=?
        """,
        (username, password)
    )

    user = cursor.fetchone()
    conn.close()

    if user:
        session["user_id"] = user[0]
        session["username"] = user[1]
        session["email"] = user[2] or ""

        return redirect("/dashboard")

    return render_template(
        "login.html",
        message="Invalid Username or Password"
    )


# =========================
# FORGOT PASSWORD
# =========================

@app.route("/forgot-password", methods=["GET"])
def forgot_password_page():
    return render_template("forgot_password.html")


@app.route("/forgot-password", methods=["POST"])
def forgot_password():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not username or not email or not new_password:
        return render_template(
            "forgot_password.html",
            message="Please fill all fields."
        )

    if new_password != confirm_password:
        return render_template(
            "forgot_password.html",
            message="Passwords do not match."
        )

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE username=? AND email=?
        """,
        (username, email)
    )

    user = cursor.fetchone()

    if not user:
        conn.close()

        return render_template(
            "forgot_password.html",
            message="Username and email do not match."
        )

    cursor.execute(
        """
        UPDATE users
        SET password=?
        WHERE id=?
        """,
        (new_password, user[0])
    )

    conn.commit()
    conn.close()

    return render_template(
        "login.html",
        message="Password reset successfully! Please login."
    )


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, date, category, amount, description
        FROM expenses
        WHERE user_id=?
        ORDER BY id DESC
        """,
        (user_id,)
    )

    expenses = cursor.fetchall()

    cursor.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id=?
        """,
        (user_id,)
    )

    total = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT category, SUM(amount)
        FROM expenses
        WHERE user_id=?
        GROUP BY category
        ORDER BY SUM(amount) DESC
        """,
        (user_id,)
    )

    category_totals = cursor.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        expenses=expenses,
        total=total,
        category_totals=category_totals
    )


# =========================
# EXPENSES
# =========================

@app.route("/expenses")
def expenses_page():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, date, category, amount, description
        FROM expenses
        WHERE user_id=?
        ORDER BY id DESC
        """,
        (user_id,)
    )

    expenses = cursor.fetchall()

    cursor.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id=?
        """,
        (user_id,)
    )

    total = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "expenses.html",
        expenses=expenses,
        total=total
    )


# =========================
# ADD EXPENSE PAGE
# =========================

@app.route("/add-expense")
def add_expense_page():
    if "user_id" not in session:
        return redirect("/login")

    return render_template("add_expense.html")


# =========================
# ADD EXPENSE
# =========================

@app.route("/add_expense", methods=["POST"])
def add_expense():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    date = request.form.get("date", "")
    category = request.form.get("category", "").strip()
    amount = request.form.get("amount", "")
    description = request.form.get("description", "").strip()

    if not date or not category or not amount:
        return render_template(
            "add_expense.html",
            message="Please fill all required fields."
        )

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO expenses(
            user_id,
            date,
            category,
            amount,
            description
        )
        VALUES(?,?,?,?,?)
        """,
        (
            user_id,
            date,
            category,
            amount,
            description
        )
    )

    try:
        cursor.execute(
            """
            INSERT INTO categories(user_id, name)
            VALUES(?,?)
            """,
            (user_id, category)
        )
    except sqlite3.Error:
        pass

    conn.commit()
    conn.close()

    return redirect("/expenses")


# =========================
# SEARCH
# =========================

@app.route("/search", methods=["POST"])
def search():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    category = request.form.get("category", "").strip()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, date, category, amount, description
        FROM expenses
        WHERE user_id=?
        AND category LIKE ?
        ORDER BY id DESC
        """,
        (
            user_id,
            "%" + category + "%"
        )
    )

    expenses = cursor.fetchall()

    cursor.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id=?
        """,
        (user_id,)
    )

    total = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "expenses.html",
        expenses=expenses,
        total=total,
        search=category
    )


# =========================
# EDIT EXPENSE
# =========================

@app.route("/edit/<int:id>")
def edit(id):
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, date, category, amount, description
        FROM expenses
        WHERE id=?
        AND user_id=?
        """,
        (id, user_id)
    )

    expense = cursor.fetchone()

    conn.close()

    if expense is None:
        return redirect("/expenses")

    return render_template(
        "edit_expense.html",
        expense=expense
    )


# =========================
# UPDATE EXPENSE
# =========================

@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    date = request.form.get("date", "")
    category = request.form.get("category", "").strip()
    amount = request.form.get("amount", "")
    description = request.form.get("description", "").strip()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE expenses
        SET date=?,
            category=?,
            amount=?,
            description=?
        WHERE id=?
        AND user_id=?
        """,
        (
            date,
            category,
            amount,
            description,
            id,
            user_id
        )
    )

    try:
        cursor.execute(
            """
            INSERT INTO categories(user_id, name)
            VALUES(?,?)
            """,
            (user_id, category)
        )
    except sqlite3.Error:
        pass

    conn.commit()
    conn.close()

    return redirect("/expenses")


# =========================
# DELETE EXPENSE
# =========================

@app.route("/delete/<int:id>")
def delete(id):
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM expenses
        WHERE id=?
        AND user_id=?
        """,
        (id, user_id)
    )

    conn.commit()
    conn.close()

    return redirect("/expenses")


# =========================
# CATEGORIES
# =========================

@app.route("/categories")
def categories():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            category,
            COUNT(*),
            COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id=?
        GROUP BY category
        ORDER BY SUM(amount) DESC
        """,
        (user_id,)
    )

    category_data = cursor.fetchall()

    conn.close()

    return render_template(
        "categories.html",
        category_data=category_data
    )


# =========================
# REPORTS
# =========================

@app.route("/reports")
def reports():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT category, SUM(amount)
        FROM expenses
        WHERE user_id=?
        GROUP BY category
        ORDER BY SUM(amount) DESC
        """,
        (user_id,)
    )

    category_totals = cursor.fetchall()

    cursor.execute(
        """
        SELECT
            substr(date, 1, 7) AS month,
            SUM(amount)
        FROM expenses
        WHERE user_id=?
        GROUP BY substr(date, 1, 7)
        ORDER BY month DESC
        """,
        (user_id,)
    )

    monthly_totals = cursor.fetchall()

    cursor.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id=?
        """,
        (user_id,)
    )

    total = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "reports.html",
        category_totals=category_totals,
        monthly_totals=monthly_totals,
        total=total
    )


# =========================
# PROFILE
# =========================

@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, username, email
        FROM users
        WHERE id=?
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    conn.close()

    return render_template(
        "profile.html",
        user=user
    )


# =========================
# UPDATE PROFILE
# =========================

@app.route("/update-profile", methods=["POST"])
def update_profile():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE users
            SET username=?,
                email=?
            WHERE id=?
            """,
            (
                username,
                email,
                user_id
            )
        )

        conn.commit()

        session["username"] = username
        session["email"] = email

        message = "Profile updated successfully."

    except sqlite3.IntegrityError:
        message = "Username already exists."

    conn.close()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, username, email
        FROM users
        WHERE id=?
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    conn.close()

    return render_template(
        "profile.html",
        user=user,
        message=message
    )


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# =========================
# RUN APP
# =========================

if __name__ == "__main__":
    app.run(debug=True)