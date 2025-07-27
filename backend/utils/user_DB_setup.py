import os
import bcrypt
import base64
from tinydb import TinyDB
from datetime import datetime

# Initialize TinyDB (this will create the user database file in config folder)
db = TinyDB(os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'users.json')) # Path to save in config folder

# Hash password function (with base64 encoding)
def hash_password(password):
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    # Convert bytes to a base64 string for storage
    return base64.b64encode(hashed_password).decode('utf-8')

# Users data (you can add your users here)
users = [
    {"username": "jack", "password": "4*#*#*#*#*#", "role": "admin"},
    {"username": "admin", "password": "8*#*#*#*#i", "role": "admin"},
    {"username": "millie", "password": "s#*#*#*#m", "role": "user"},
    {"username": "demi", "password": "s*#*#*#*#*#*#*b", "role": "user"},
    {"username": "gabby", "password": "s*#*#*#*#*#*#*s", "role": "user"},
    #{"username": "user4", "password": "userpassword4", "role": "user"},
    #{"username": "user5", "password": "userpassword5", "role": "user"},
    #{"username": "user6", "password": "userpassword6", "role": "user"},
    #{"username": "user7", "password": "userpassword7", "role": "user"},
    #{"username": "user8", "password": "userpassword8", "role": "user"},
    #{"username": "user9", "password": "userpassword9", "role": "user"},
    {"username": "user10", "password": "", "role": "user"}
]

# Insert users into the database with hashed passwords
for user in users:
    user_data = {
        'username': user['username'],
        'password': hash_password(user['password']),  # Store hashed password
        'role': user['role'],
        'settings': {},  # Empty settings dictionary
        'last_login': None,  # Will be updated upon login
        'notifications': []  # Empty list for notifications
    }
    db.insert(user_data)
    print(f"User '{user['username']}' added successfully!")




