from flask import Flask, render_template, request, send_file, session, redirect, url_for, flash
import os
import sqlite3
from encryption import encrypt_image, decrypt_image
from auth import auth_bp
from config import ENCRYPTED_FOLDER, DECRYPTED_FOLDER, UPLOAD_FOLDER, SECRET_KEY, DATABASE_NAME
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

# Register authentication blueprint
app.register_blueprint(auth_bp, url_prefix="/auth")

# Redirect unauthenticated users to login
@app.route("/", methods=["GET", "POST"])
def index():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    encrypted_filename = None
    if request.method == "POST":
        file = request.files.get("file")
        category = request.form.get("category")
        if file and category:
            safe_filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, safe_filename)

            encrypted_filename = "enc_" + safe_filename
            encrypted_path = os.path.join(ENCRYPTED_FOLDER, encrypted_filename)

            file.save(file_path)
            key = session.get("key", None)
            if key:
                encrypt_image(file_path, encrypted_path, key)
                # Save file info into database
                conn = sqlite3.connect(DATABASE_NAME)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO uploads (username, filename, category) VALUES (?, ?, ?)",
                    (session["user"], encrypted_filename, category),
                )
                conn.commit()
                conn.close()
                flash(f"File uploaded and encrypted under {category} category!", "success")
            else:
                flash("No encryption key found!", "danger")
        else:
            flash("Please select a file and category!", "danger")

    return render_template("index.html", encrypted=encrypted_filename)


# Decryption Route
@app.route("/view", methods=["GET", "POST"])
def view():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    decrypted_filename = None
    error_message = None

    if request.method == "POST":
        file = request.files.get("file")
        if file:
            safe_filename = secure_filename(file.filename)
            encrypted_path = os.path.join(ENCRYPTED_FOLDER, safe_filename)

            # Remove 'enc_' prefix for decrypted file
            decrypted_filename = "dec_" + safe_filename[4:]
            decrypted_path = os.path.join(DECRYPTED_FOLDER, decrypted_filename)

            file.save(encrypted_path)
            key = session.get("key", None)
            if key:
                if not decrypt_image(encrypted_path, decrypted_path, key):
                    error_message = "Decryption failed! Invalid file or wrong key."
            else:
                error_message = "No decryption key found in session!"

    return render_template("view.html", decrypted=decrypted_filename, error=error_message)


# File Download Route
@app.route("/download/<file_type>/<filename>")
def download(file_type, filename):
    folder = ENCRYPTED_FOLDER if file_type == "encrypted" else DECRYPTED_FOLDER
    file_path = os.path.join(folder, filename)

    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash("File not found!", "danger")
        return redirect(url_for("index"))


# Dashboard Route
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT filename, category FROM uploads WHERE username = ?", (session["user"],))
    files = cursor.fetchall()
    conn.close()

    categories = {}
    for filename, category in files:
        categories.setdefault(category, []).append(filename)

    return render_template("dashboard.html", categories=categories)


# Delete File Route
@app.route("/delete/<filename>", methods=["POST"])
def delete_file(filename):
    if "user" not in session:
        return redirect(url_for("auth.login"))

    safe_filename = secure_filename(filename)
    file_path = os.path.join(ENCRYPTED_FOLDER, safe_filename)

    # Delete file from disk
    if os.path.exists(file_path):
        os.remove(file_path)

    # Delete from database
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM uploads WHERE username = ? AND filename = ?",
        (session["user"], safe_filename),
    )
    conn.commit()
    conn.close()

    # Trigger SweetAlert in dashboard.html
    flash("deleted", "success")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True)

