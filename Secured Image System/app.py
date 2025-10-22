from flask import Flask, render_template, request, send_file, session, redirect, url_for, flash
import os
import sqlite3
import hashlib
import datetime
from encryption import encrypt_image, decrypt_image
from auth import auth_bp
from config import ENCRYPTED_FOLDER, DECRYPTED_FOLDER, UPLOAD_FOLDER, SECRET_KEY, DATABASE_NAME
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

# Register authentication blueprint
app.register_blueprint(auth_bp, url_prefix="/auth")

# Ensure folders exist
for folder in [UPLOAD_FOLDER, ENCRYPTED_FOLDER, DECRYPTED_FOLDER]:
    os.makedirs(folder, exist_ok=True)


# Home / Upload page
@app.route("/", methods=["GET", "POST"])
def index():
    if "user" not in session:
        return redirect(url_for("auth.register"))

    encrypted_filename = None
    if request.method == "POST":
        file = request.files.get("file")
        category = request.form.get("category", "default")
        if file:
            safe_filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, safe_filename)

            encrypted_filename = "enc_" + safe_filename
            encrypted_path = os.path.join(ENCRYPTED_FOLDER, encrypted_filename)

            file.save(file_path)
            key = session.get("key")
            if key:
                encrypt_image(file_path, encrypted_path, key)
                with open(encrypted_path, "rb") as f:
                    file_bytes = f.read()
                    file_hash = hashlib.sha256(file_bytes).hexdigest()

                # Save file info into database
                conn = sqlite3.connect(DATABASE_NAME)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO uploads (username, filename, category, file_hash) VALUES (?, ?, ?, ?)",
                    (session["user"], encrypted_filename, category, file_hash),
                )
                conn.commit()
                conn.close()
                flash(f"File uploaded and encrypted under '{category}'!", "success")
            else:
                flash("No encryption key found!", "error")
        else:
            flash("Please select a file!", "error")

    return render_template("index.html", encrypted=encrypted_filename)


# Decrypt route with flash messages and full history
@app.route("/decrypt", methods=["GET", "POST"])
def decrypt():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    decrypted_filename = None
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            flash("No file selected for decryption!", "error")
            return redirect(url_for("decrypt"))

        safe_filename = secure_filename(file.filename)
        file_bytes = file.read()
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        # Verify ownership
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT filename, decrypted_history FROM uploads WHERE username=? AND file_hash=?",
            (session["user"], file_hash),
        )
        result = cursor.fetchone()

        if not result:
            flash("You do not own this encrypted file!", "error")
            conn.close()
            return redirect(url_for("decrypt"))

        decrypted_filename = "dec_" + safe_filename
        decrypted_path = os.path.join(DECRYPTED_FOLDER, decrypted_filename)
        temp_path = os.path.join(UPLOAD_FOLDER, safe_filename)
        with open(temp_path, "wb") as f:
            f.write(file_bytes)

        key = session.get("key")
        if not key:
            flash("No decryption key found in session!", "error")
            conn.close()
            return redirect(url_for("decrypt"))

        try:
            success = decrypt_image(temp_path, decrypted_path, key)
            if not success:
                flash("Decryption failed! Wrong key or corrupted file.", "error")
                conn.close()
                return redirect(url_for("decrypt"))

            flash("File decrypted successfully!", "success")

            # Append new decryption record with timestamp
            now = datetime.datetime.now().strftime("%H:%M on %d-%m-%Y")
            existing_history = result[1] or ""
            if existing_history:
                new_history = existing_history + f", {decrypted_filename} at {now}"
            else:
                new_history = f"{decrypted_filename} at {now}"

            cursor.execute(
                "UPDATE uploads SET decrypted_history=? WHERE username=? AND file_hash=?",
                (new_history, session["user"], file_hash),
            )
            conn.commit()
            conn.close()

        except Exception as e:
            flash(f"An error occurred during decryption: {str(e)}", "error")
            conn.close()
            return redirect(url_for("decrypt"))

    return render_template("decrypt.html", decrypted=decrypted_filename)


# Download route
@app.route("/download/<file_type>/<filename>")
def download(file_type, filename):
    folder = ENCRYPTED_FOLDER if file_type == "encrypted" else DECRYPTED_FOLDER
    file_path = os.path.join(folder, filename)

    if os.path.exists(file_path):
        if file_type == "decrypted" and "user" in session:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT decrypted_history FROM uploads WHERE username=? AND decrypted_history LIKE ?",
                (session["user"], f"%{filename}%"),
            )
            result = cursor.fetchone()
            if result and "&downloaded" not in result[0]:
                new_history = result[0] + "&downloaded"
                cursor.execute(
                    "UPDATE uploads SET decrypted_history=? WHERE username=? AND decrypted_history LIKE ?",
                    (new_history, session["user"], f"%{filename}%"),
                )
                conn.commit()
            conn.close()
        return send_file(file_path, as_attachment=True)
    else:
        flash("File not found!", "error")
        return redirect(url_for("index"))


# Dashboard for encrypted files
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT filename, category FROM uploads WHERE username=?", (session["user"],))
    files = cursor.fetchall()
    conn.close()

    categories = {}
    for filename, category in files:
        categories.setdefault(category, []).append(filename)

    return render_template("dashboard.html", categories=categories)


# Delete file route
@app.route("/delete/<filename>", methods=["POST"])
def delete_file(filename):
    if "user" not in session:
        return redirect(url_for("auth.login"))

    safe_filename = secure_filename(filename)
    file_path = os.path.join(ENCRYPTED_FOLDER, safe_filename)

    if os.path.exists(file_path):
        os.remove(file_path)

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM uploads WHERE username=? AND filename=?",
        (session["user"], safe_filename),
    )
    conn.commit()
    conn.close()

    flash("File deleted successfully!", "success")
    return redirect(url_for("dashboard"))


# Decryption History
@app.route("/history")
def history():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT decrypted_history FROM uploads WHERE username=? AND decrypted_history != ''",
        (session["user"],),
    )
    rows = cursor.fetchall()
    conn.close()

    files = []
    for row in rows:
        entries = row[0].split(",")  # Split multiple decryption events
        for entry in entries:
            clean_entry = entry.replace("&downloaded", "").strip()
            files.append(clean_entry)

    # Sort by timestamp
    def get_datetime(entry):
        # Entry format: "dec_filename at HH:MM on DD-MM-YYYY"
        try:
            parts = entry.split(" at ")
            dt_str = parts[1] if len(parts) > 1 else ""
            return datetime.datetime.strptime(dt_str, "%H:%M on %d-%m-%Y")
        except:
            return datetime.datetime.min

    files.sort(key=get_datetime)

    return render_template("history.html", files=files)

if __name__ == "__main__":
    app.run(debug=True)
