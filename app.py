from flask import Flask, render_template, request, redirect
import sqlite3
import re
from datetime import datetime

app = Flask(__name__)

# -----------------------------
# Create Database and Table
# -----------------------------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

init_db()

# Duplicate attempt counter
duplicate_count = 0


# -----------------------------
# Home Page
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def home():

    global duplicate_count

    message = ""
    message_class = ""

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        phone = request.form["phone"].strip()

        # -----------------------------
        # Email Validation
        # -----------------------------
        email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'

        # Indian Mobile Number
        phone_pattern = r'^[6-9]\d{9}$'

        if not re.match(email_pattern, email):
            message = "Invalid Email Format"
            message_class = "warning"

        elif not re.match(phone_pattern, phone):
            message = "Invalid Phone Number"
            message_class = "warning"

        else:

            # -----------------------------
            # Duplicate Check
            # -----------------------------
            c.execute(
                "SELECT * FROM users WHERE email=? AND phone=?",
                (email, phone)
            )

            duplicate = c.fetchone()

            if duplicate:

                duplicate_count += 1

                message = "Duplicate Record Found"
                message_class = "error"

            else:

                # -----------------------------
                # False Positive Check
                # -----------------------------

                c.execute(
                    "SELECT * FROM users WHERE email=?",
                    (email,)
                )

                email_exist = c.fetchone()

                c.execute(
                    "SELECT * FROM users WHERE phone=?",
                    (phone,)
                )

                phone_exist = c.fetchone()

                if email_exist or phone_exist:

                    status = "False Positive"

                    message = "False Positive Detected"

                    message_class = "warning"

                else:

                    status = "Unique"

                    message = "Unique Record Added"

                    message_class = "success"

                created_at = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

                c.execute("""
                INSERT INTO users
                (name,email,phone,status,created_at)
                VALUES(?,?,?,?,?)
                """,
                (
                    name,
                    email,
                    phone,
                    status,
                    created_at
                ))

                conn.commit()

    # -----------------------------
    # Dashboard Counts
    # -----------------------------

    c.execute("SELECT COUNT(*) FROM users")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM users WHERE status='Unique'")
    unique = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM users WHERE status='False Positive'")
    false_positive = c.fetchone()[0]

    conn.close()

    return render_template(
        "index.html",
        message=message,
        message_class=message_class,
        total=total,
        unique=unique,
        duplicate=duplicate_count,
        false_positive=false_positive
    )


# -----------------------------
# Records Page
# -----------------------------
@app.route("/records")
def records():

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    SELECT *
    FROM users
    ORDER BY id DESC
    """)

    data = c.fetchall()

    conn.close()

    return render_template(
        "records.html",
        records=data
    )
@app.route("/delete/<int:id>")
def delete_record(id):

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("DELETE FROM users WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/records")

# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)