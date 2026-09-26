import os
from datetime import datetime, timezone
from bson.objectid import ObjectId
from bson.errors import InvalidId

from fastapi import FastAPI, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pymongo import MongoClient
import bcrypt
import requests

app = FastAPI(title="Interform Inc. Platform", version="1.0.0")

# MongoDB Bağlantısı
MONGO_URI = os.environ.get("MONGO_URI", "")
DB_NAME = os.environ.get("DB_NAME", "interform_db")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

users_col = db["users"]
logs_col = db["logs"]
special_accounts_col = db["special_accounts"]
cheats_col = db["cheats"]
store_col = db["store_products"]

# Admin Tanımlamaları
ADMIN_USERNAME = "Administrator"
ADMIN_PASSWORD = "admin123"
ADMIN_INTERNAL_EMAIL = "administrator"

# Groq AI Ayarları
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
SYSTEM_PROMPT = "Sen Interform Inc. şirketinin gelişmiş yapay zeka asistanısın. Türkçe konuş, kurumsal ve teknolojik bir üslup takın."

# Statik ve Şablon (HTML) Dosya Klasörleri
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def add_log(log_type, action, meta="", by=""):
    try:
        logs_col.insert_one({
            "type": log_type,
            "action": action,
            "meta": meta,
            "by": by,
            "time": now_iso(),
        })
    except Exception:
        pass

def serialize_user(u):
    return {
        "name": u.get("name"),
        "email": u.get("email"),
        "role": u.get("role", "user"),
        "joinDate": u.get("joinDate"),
    }

def ensure_admin_accounts():
    if ADMIN_PASSWORD:
        existing = users_col.find_one({"email": ADMIN_INTERNAL_EMAIL})
        hashed_pw = bcrypt.hashpw(ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        if existing:
            users_col.update_one(
                {"email": ADMIN_INTERNAL_EMAIL},
                {"$set": {"name": ADMIN_USERNAME, "role": "administrator", "passwordHash": hashed_pw}}
            )
        else:
            users_col.insert_one({
                "name": ADMIN_USERNAME,
                "email": ADMIN_INTERNAL_EMAIL,
                "passwordHash": hashed_pw,
                "role": "administrator",
                "joinDate": now_iso(),
            })

ensure_admin_accounts()

# Pydantic Modelleri
class RegisterModel(BaseModel):
    name: str
    email: str
    password: str

class LoginModel(BaseModel):
    email: str
    password: str

class ChatModel(BaseModel):
    messages: list

# --- HTML SAYFA ROTALARI (GÜNCELLENDİ) ---
@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    return templates.TemplateResponse(request, "index.html", {})

# --- KULLANICI & AUTH API'LERİ ---
@app.post("/api/register")
async def register(data: RegisterModel):
    name = data.name.strip()
    email = data.email.strip().lower()
    password = data.password

    if not name or not email or not password:
        raise HTTPException(status_code=400, detail="Tüm alanları doldurun.")
    if len(password) < 4:
        raise HTTPException(status_code=400, detail="Şifre en az 4 karakter olmalı.")
    if users_col.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı.")

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    users_col.insert_one({
        "name": name,
        "email": email,
        "passwordHash": hashed_password,
        "role": "user",
        "joinDate": now_iso(),
    })
    add_log("sistem", f"{name} kayıt oldu.", email)
    return {"success": True}

@app.post("/api/login")
async def login(data: LoginModel):
    identifier = data.email.strip().lower()
    password = data.password

    if identifier in [ADMIN_USERNAME.lower(), ADMIN_INTERNAL_EMAIL]:
        if password != ADMIN_PASSWORD:
            raise HTTPException(status_code=401, detail="ACCESS DENIED")
        ensure_admin_accounts()
        u = users_col.find_one({"email": ADMIN_INTERNAL_EMAIL})
        return {"user": serialize_user(u)}

    u = users_col.find_one({"email": identifier})
    if not u or not bcrypt.checkpw(password.encode('utf-8'), u.get("passwordHash", "").encode('utf-8')):
        raise HTTPException(status_code=401, detail="ACCESS DENIED")

    return {"user": serialize_user(u)}

@app.get("/api/users")
async def list_users():
    users = [serialize_user(u) for u in users_col.find().sort("joinDate", -1)]
    return users

# --- YAPAY ZEKA SOHBET API'Sİ ---
@app.post("/chat")
async def chat(data: ChatModel):
    messages = data.messages
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY tanımlı değil.")

    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    try:
        resp = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": full_messages,
                "temperature": 0.8,
            },
            timeout=60,
        )
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- İNJECTOR & KATEGORİLER API'Sİ ---
@app.get("/api/cheats")
async def get_cheats():
    cheats = list(cheats_col.find().sort("game", 1))
    for c in cheats:
        c["_id"] = str(c["_id"])
    return cheats

@app.post("/api/cheats")
async def add_cheat(data: dict):
    game = data.get("game")
    version = data.get("version")
    status_val = data.get("status", "Undetected")
    link = data.get("link", "#")
    
    if not game:
        raise HTTPException(status_code=400, detail="Oyun adı zorunludur.")
        
    doc = {"game": game, "version": version, "status": status_val, "link": link, "updatedAt": now_iso()}
    res = cheats_col.insert_one(doc)
    return {"success": True, "id": str(res.inserted_id)}

# --- OYUN KEYLERİ MAĞAZASI API'Sİ ---
@app.get("/api/store")
async def get_store_products():
    products = list(store_col.find().sort("title", 1))
    for p in products:
        p["_id"] = str(p["_id"])
    return products

@app.post("/api/store")
async def add_store_product(data: dict):
    title = data.get("title")
    price = data.get("price")
    category = data.get("category", "Oyun Keyi")
    
    if not title:
        raise HTTPException(status_code=400, detail="Ürün başlığı zorunludur.")
        
    doc = {"title": title, "price": price, "category": category, "time": now_iso()}
    res = store_col.insert_one(doc)
    return {"success": True, "id": str(res.inserted_id)}
