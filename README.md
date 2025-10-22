# SecureVault-Encrypted-Image-Management-System
SecureVault is a web app for secure image management. Users can upload, encrypt, decrypt, and download images while maintaining privacy. Features include user authentication, encrypted storage, categorized dashboard, and decryption history with timestamps.

🔐 Image Encryption & Decryption App

This is a Flask web application for securely encrypting and decrypting images.
It also includes user authentication, a file dashboard, and dark/light mode support.

🚀 Getting Started

First, set up a virtual environment and install dependencies:
```bash
python -m venv venv
# Activate the virtual environment:
# Mac/Linux
source venv/bin/activate
# Windows
venv\Scripts\activate

pip install -r requirements.txt
```
Run the development server:

```bash
python database.py
python app.py
```
Open [http://127.0.0.1:5000](http://127.0.0.1:5000) with your browser to see the application.

## Features

- Encrypt & Decrypt Images

- User Authentication (Register/Login/Logout) with strong passwords

- SHA-256 hashing for file verification

- Dashboard to view, download & delete files

- Decryption history with date & time

- SweetAlert2 for success/error messages
