import sqlite3
from flask import Blueprint, request, redirect, render_template, session, flash, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from config import DATABASE_NAME

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("auth.login"))
        except sqlite3.IntegrityError:
            flash("Username already taken. Try another.", "danger")
        
        conn.close()

    return render_template("register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        # user: (id, username, password_hash)
        if user and check_password_hash(user[2], password):
            session["user"] = user[1]        # username
            session["user_id"] = user[0]     # id
            session["key"] = password.encode()  # key (bytes) used for encryption
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password", "danger")

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("user_id", None)
    session.pop("key", None)
    flash("Logged out successfully.", "info")
    return redirect(url_for("auth.login"))

