import os

SECRET_KEY = os.urandom(24)
DATABASE_NAME = "users.db"
UPLOAD_FOLDER = "static/"
ENCRYPTED_FOLDER = "static/encrypted/"
DECRYPTED_FOLDER = "static/decrypted/"

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ENCRYPTED_FOLDER, exist_ok=True)
os.makedirs(DECRYPTED_FOLDER, exist_ok=True)
