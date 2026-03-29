from fastapi import FastAPI
from fastapi import Depends
from fastapi import Header
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt
from passlib.context import CryptContext
import sqlite3

SECRET_KEY = "secret123"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"])

def hash_password(pw):
    return pwd_context.hash(pw)

def verify_password(pw, hashed):
    return pwd_context.verify(pw, hashed)

def get_current_user(authorization: str = Header(None)):
    if not authorization:
        return None

    token = authorization.replace("Bearer ", "")

    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return data["user_id"]
    except:
        return None

app = FastAPI()

# CORS cho React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    return sqlite3.connect("app.db")


# tạo bảng
def init_db():
    conn = get_db()

    # bảng users
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # bảng items (có user_id)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        user_id INTEGER
    )
    """)

    conn.commit()

init_db()

@app.get("/items")
def get_items(user_id=Depends(get_current_user)):
    if not user_id:
        return []

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM items WHERE user_id=?",
        (user_id,)
    ).fetchall()

    return [{"id": r[0], "name": r[1]} for r in rows]



@app.post("/items")
def add_item(item: dict, user_id=Depends(get_current_user)):
    conn = get_db()

    conn.execute(
        "INSERT INTO items (name, user_id) VALUES (?, ?)",
        (item["name"], user_id)
    )
    conn.commit()

    return {"ok": True}

@app.post("/register")
def register(user: dict):
    conn = get_db()

    hashed = hash_password(user["password"])

    try:
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (user["username"], hashed)
        )
        conn.commit()
        return {"ok": True}
    except:
        return {"error": "user exists"}
    
@app.post("/login")   
def login(user: dict):
    conn = get_db()

    row = conn.execute(
        "SELECT * FROM users WHERE username=?",
        (user["username"],)
    ).fetchone()

    if not row:
        return {"error": "user not found"}

    if not verify_password(user["password"], row[2]):
        return {"error": "wrong password"}

    token = jwt.encode({"user_id": row[0]}, SECRET_KEY, algorithm=ALGORITHM)

    return {"access_token": token}

from fastapi import Header

def get_current_user(authorization: str = Header(None)):
    if not authorization:
        return None

    token = authorization.replace("Bearer ", "")

    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return data["user_id"]
    except:
        return None