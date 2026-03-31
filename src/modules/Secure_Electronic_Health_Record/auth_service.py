import bcrypt
from datetime import datetime
import random
import string
from db import get_db

db = get_db()

def generate_user_id():
    return "USR-" + "".join(random.choices(string.digits, k=6))

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

def signup_user(name: str, email: str, password: str, role: str) -> dict:
    existing = db.users.find_one({"email": email})
    if existing:
        return {"success": False, "message": "Email already registered!"}
    user_id = generate_user_id()
    db.users.insert_one({
        "user_id":    user_id,
        "name":       name,
        "email":      email,
        "password":   hash_password(password),
        "role":       role,
        "created_at": datetime.now().isoformat()
    })
    return {"success": True, "message": f"Account created! Your User ID is {user_id}", "user_id": user_id}

def login_user(email: str, password: str, role: str) -> dict:
    user = db.users.find_one({"email": email, "role": role})
    if not user:
        return {"success": False, "message": "No account found with this email and role!"}
    if not verify_password(password, user["password"]):
        return {"success": False, "message": "Incorrect password!"}
    return {
        "success": True,
        "user_id": user["user_id"],
        "name":    user["name"],
        "role":    user["role"],
        "email":   user["email"]
    }
