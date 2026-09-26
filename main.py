from fastapi import FastAPI, Request, HTTPException, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from groq import Groq

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# --- VERİTABANI / BELLEK SİMÜLASYONU ---
# 10 Kademeli Rütbe Listesi
RANKS = [
    "Administrator",
    "Yönetim Kurulu",
    "BT Genel Sorumlu",
    "Mağaza Genel Sorumlu",
    "Mağaza Yetkilisi",
    "BT Yetkilisi",
    "Genel Yetkili",
    "Yetkili",
    "Stajyer",
    "Üye"
]

# Kullanıcı Veritabanı (Bellekte)
USERS = {
    "admin@interform.inc": {
        "password": "admin123",
        "role": "Administrator",
        "name": "Sistem Admin"
    }
}

# Mağaza Ürünleri
PRODUCTS = [
    {"id": 1, "name": "Cyberpunk Neural Link v1", "price": 299.99, "category": "Donanım", "stock": 14},
    {"id": 2, "name": "Quantum Encryption Key", "price": 149.50, "category": "Yazılım", "stock": 42},
    {"id": 3, "name": "AI Sentinel Core", "price": 599.00, "category": "AI Modülü", "stock": 5}
]

# --- ANA SAYFA ---
@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})

# --- KİMLİK DOĞRULAMA & KAYIT ENDPOINTLERİ ---
@app.post("/api/register")
async def api_register(request: Request):
    data = await request.json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    name = data.get("name", "Yeni Üye")

    if not email or not password:
        raise HTTPException(status_code=400, detail="E-posta ve şifre zorunludur.")
    
    if email in USERS:
        raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kayıtlı.")

    # Yeni kullanıcıya otomatik 'Üye' rütbesi atanır
    USERS[email] = {
        "password": password,
        "role": "Üye",
        "name": name
    }
    return {"status": "success", "message": "Kayıt başarılı. Giriş yapabilirsiniz."}

@app.post("/api/login")
async def api_login(request: Request):
    data = await request.json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = USERS.get(email)
    if not user or user["password"] != password:
        raise HTTPException(status_code=400, detail="Geçersiz e-posta veya şifre.")

    # Rolüne göre yönlendirme
    if user["role"] == "Administrator" or "Yönetim" in user["role"] or "Sorumlu" in user["role"]:
        redirect_url = "/admin-dashboard"
    else:
        redirect_url = "/dashboard"

    return {"status": "success", "role": user["role"], "redirect": redirect_url, "email": email}

# --- RÜTBE GÜNCELLEME ENDPOINTİ ---
@app.post("/api/admin/update-rank")
async def update_user_rank(request: Request):
    data = await request.json()
    target_email = data.get("email", "").strip().lower()
    new_rank = data.get("rank", "")
    admin_secret = data.get("adminSecret", "")

    if new_rank not in RANKS:
        raise HTTPException(status_code=400, detail="Geçersiz rütbe seviyesi.")

    if new_rank == "Administrator" and admin_secret != "admin123":
        raise HTTPException(status_code=403, detail="Administrator rütbesi atamak için geçerli admin şifresi gerekli!")

    if target_email not in USERS:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    USERS[target_email]["role"] = new_rank
    return {"status": "success", "message": f"{target_email} adlı kullanıcının rütbesi {new_rank} olarak güncellendi."}

# --- MAĞAZA ÜRÜN EKLEME ENDPOINTİ (YÖNETİCİLER İÇİN) ---
@app.post("/api/admin/add-product")
async def add_product(request: Request):
    data = await request.json()
    name = data.get("name")
    price = float(data.get("price", 0))
    category = data.get("category", "Genel")
    stock = int(data.get("stock", 10))

    new_id = len(PRODUCTS) + 1
    PRODUCTS.append({
        "id": new_id,
        "name": name,
        "price": price,
        "category": category,
        "stock": stock
    })
    return {"status": "success", "message": "Ürün başarıyla mağazaya eklendi."}

# --- YAPAY ZEKA ENDPOINTİ (Qwen Model) ---
@app.post("/api/ai-query")
async def ai_query(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {"response": "[SİSTEM UYARISI]: GROQ_API_KEY bulunamadı! Simüle Yanıt: Sistemler normal çalışıyor."}
    
    try:
        client = Groq(api_key=api_key)
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Sen Interform Inc. kurumsal yapay zeka asistanısın. Kullanıcılara teknik destek, ürün bilgileri ve sistem durumu hakkında yardımcı oluyorsun."},
                {"role": "user", "content": prompt}
            ],
            model="qwen/qwen3.8-27b",
        )
        return {"response": chat_completion.choices[0].message.content}
    except Exception as e:
        return {"response": f"AI Servis Hatası: {str(e)}"}

# --- MAĞAZA ROTALARI ---
@app.get("/store", response_class=HTMLResponse)
async def store_page():
    return """
    <html>
        <head>
            <title>Interform Inc. | Mağaza</title>
            <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@400;600&display=swap" rel="stylesheet">
            <style>
                body { background: #070707; color: #fff; font-family: 'Rajdhani', sans-serif; padding: 40px; }
                .container { max-width: 1100px; margin: 0 auto; }
                .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 30px; }
                .card { background: #111; border: 1px solid #262626; padding: 20px; }
                .btn { background: #3a86ff; color: #fff; border: none; padding: 10px 15px; font-family: 'Orbitron'; cursor: pointer; margin-top: 10px; width: 100%; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1 style="font-family:'Orbitron'; color:#3a86ff;">// INTERFORM MAĞAZA</h1>
                <a href="/" style="color:#aaa; text-decoration:none;">&larr; Ana Sayfa</a>
                <div class="grid" id="productGrid"></div>
            </div>
            <script>
                fetch('/api/products').then(res => res.json()).then(data => {
                    const grid = document.getElementById('productGrid');
                    data.products.forEach(p => {
                        grid.innerHTML += `
                            <div class="card">
                                <h3 style="font-family:'Orbitron';">${p.name}</h3>
                                <p style="color:#aaa;">Kategori: ${p.category}</p>
                                <p style="color:#4caf7d; font-size:1.2rem; font-weight:bold;">$${p.price}</p>
                                <p>Stok: ${p.stock}</p>
                                <button class="btn" onclick="alert('${p.name} sepete eklendi!')">SEPETE EKLE</button>
                            </div>
                        `;
                    });
                });
                fetch('/api/products').then(res => res.json()).catch(() => {});
            </script>
        </body>
    </html>
    """

# Ürün listeleme API
@app.get("/api/products")
async def get_products():
    return {"products": PRODUCTS}

# --- KULLANICI PANELI (AI Erişimi Var) ---
@app.get("/dashboard", response_class=HTMLResponse)
async def user_dashboard():
    return """
    <html>
        <head>
            <title>Interform | Kullanıcı Portali</title>
            <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@400;600&display=swap" rel="stylesheet">
            <style>
                body { background: #070707; color: #fff; font-family: 'Rajdhani', sans-serif; padding: 30px; }
                .box { max-width: 800px; margin: 0 auto; background: #111; border: 1px solid #262626; padding: 30px; }
                .chat { background: #000; height: 300px; border: 1px solid #262626; padding: 15px; overflow-y: auto; margin-top: 15px; }
                input, button { padding: 10px; font-family: inherit; }
                input { width: 75%; background: #000; color: #fff; border: 1px solid #262626; }
                button { width: 22%; background: #3a86ff; color: #fff; border: none; cursor: pointer; font-family: 'Orbitron'; }
            </style>
        </head>
        <body>
            <div class="box">
                <h1 style="font-family:'Orbitron'; color:#3a86ff;">// KULLANICI & AI PORTALI</h1>
                <p>Hoş geldiniz. Yapay zeka asistanından destek alabilir veya mağazayı ziyaret edebilirsiniz.</p>
                <a href="/store" style="color:#3a86ff;">Mağazaya Git</a> | <a href="/" style="color:#aaa;">Çıkış Yap</a>
                
                <h3 style="font-family:'Orbitron'; margin-top:20px;">🤖 Qwen AI Asistanı</h3>
                <div class="chat" id="chatBox"><div style="color:#888;">AI Asistan hazır. Sorunuzu yazın...</div></div>
                <div style="margin-top:10px; display:flex; gap:10px;">
                    <input type="text" id="prompt" placeholder="AI'ya bir şeyler sor...">
                    <button onclick="sendAI()">GÖNDER</button>
                </div>
            </div>
            <script>
                async function sendAI() {
                    const p = document.getElementById('prompt').value;
                    const box = document.getElementById('chatBox');
                    if(!p) return;
                    box.innerHTML += `<div><b>Sen:</b> ${p}</div>`;
                    document.getElementById('prompt').value = '';
                    const res = await fetch('/api/ai-query', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({prompt: p})
                    });
                    const data = await res.json();
                    box.innerHTML += `<div style="color:#3a86ff; margin-top:5px;"><b>AI:</b> ${data.response}</div>`;
                    box.scrollTop = box.scrollHeight;
                }
            </script>
        </body>
    </html>
    """

# --- YÖNETİCİ PANELİ (Ürün Ekleme & Rütbe Yönetimi) ---
@app.get("/admin-dashboard", response_class=HTMLResponse)
async def admin_dashboard():
    return """
    <html>
        <head>
            <title>Interform | Yönetici Paneli</title>
            <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@400;600&display=swap" rel="stylesheet">
            <style>
                body { background: #070707; color: #fff; font-family: 'Rajdhani', sans-serif; padding: 30px; }
                .container { max-width: 900px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px; }
                .panel { background: #111; border: 1px solid #262626; padding: 20px; }
                input, select, button { padding: 10px; margin-top: 8px; width: 100%; background: #000; color: #fff; border: 1px solid #262626; font-family: inherit; }
                button { background: #ff007f; font-family: 'Orbitron'; font-weight: bold; cursor: pointer; }
                button:hover { opacity: 0.9; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1 style="font-family:'Orbitron'; color:#ff007f;">// YÖNETİCİ KONTROL MERKEZİ</h1>
                <a href="/store" style="color:#3a86ff;">Mağazayı Görüntüle</a> | <a href="/" style="color:#aaa;">Güvenli Çıkış</a>

                <!-- Mağaza Ürün Ekleme Paneli -->
                <div class="panel">
                    <h3 style="font-family:'Orbitron'; color:#3a86ff;">📦 Mağazaya Ürün Ekle</h3>
                    <input type="text" id="pName" placeholder="Ürün Adı">
                    <input type="number" id="pPrice" placeholder="Fiyat ($)">
                    <input type="text" id="pCategory" placeholder="Kategori (Donanım/Yazılım vb.)">
                    <input type="number" id="pStock" placeholder="Stok Adedi">
                    <button onclick="addProduct()">ÜRÜNÜ EKLE</button>
                </div>

                <!-- Rütbe Atama Paneli -->
                <div class="panel">
                    <h3 style="font-family:'Orbitron'; color:#ff007f;">🛡️ E-posta ile Rütbe Ver</h3>
                    <input type="text" id="targetEmail" placeholder="Kullanıcı E-postası">
                    <select id="targetRank">
                        <option value="Yönetim Kurulu">Yönetim Kurulu</option>
                        <option value="BT Genel Sorumlu">BT Genel Sorumlu</option>
                        <option value="Mağaza Genel Sorumlu">Mağaza Genel Sorumlu</option>
                        <option value="Mağaza Yetkilisi">Mağaza Yetkilisi</option>
                        <option value="BT Yetkilisi">BT Yetkilisi</option>
                        <option value="Genel Yetkili">Genel Yetkili</option>
                        <option value="Yetkili">Yetkili</option>
                        <option value="Stajyer">Stajyer</option>
                        <option value="Üye">Üye</option>
                        <option value="Administrator">Administrator (Özel Şifre Gerekli)</option>
                    </select>
                    <input type="password" id="adminSecret" placeholder="Admin Şifresi (Sadece Administrator için)">
                    <button onclick="updateRank()">RÜTKEYİ GÜNCELLE</button>
                </div>
            </div>

            <script>
                async function addProduct() {
                    const name = document.getElementById('pName').value;
                    const price = document.getElementById('pPrice').value;
                    const category = document.getElementById('pCategory').value;
                    const stock = document.getElementById('pStock').value;
                    
                    const res = await fetch('/api/admin/add-product', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({name, price, category, stock})
                    });
                    const data = await res.json();
                    alert(data.message);
                }

                async function updateRank() {
                    const email = document.getElementById('targetEmail').value;
                    const rank = document.getElementById('targetRank').value;
                    const adminSecret = document.getElementById('adminSecret').value;

                    const res = await fetch('/api/admin/update-rank', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({email, rank, adminSecret})
                    });
                    const data = await res.json();
                    if(res.ok) alert(data.message);
                    else alert("Hata: " + data.detail);
                }
            </script>
        </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
