from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from groq import Groq

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# --- SİSTEM DURUMU ---
SYSTEM_STATE = {
    "status": "STABİL",
    "cpu": "14.2%",
    "ram": "3.8 GB / 16 GB",
    "active_threats": 0,
    "memory_leak_simulated": False
}

# Steam Aile Paylaşımı Mağaza Envanteri
STEAM_ACCOUNTS = [
    {"id": 1, "name": "Red Dead Redemption 2 (Steam Çevrimdışı/Aile)", "price": 59.99, "category": "AAA Oyun", "stock": 8, "type": "Steam Aile Paylaşımı"},
    {"id": 2, "name": "Grand Theft Auto V (Enhanced Edition)", "price": 39.99, "category": "AAA Oyun", "stock": 15, "type": "Steam Aile Paylaşımı"},
    {"id": 3, "name": "RV There Yet? (Co-Op / Indie)", "price": 19.99, "category": "İndie", "stock": 22, "type": "Steam Aile Paylaşımı"},
    {"id": 4, "name": "Cyberpunk 2077 + Phantom Liberty", "price": 89.99, "category": "AAA Oyun", "stock": 5, "type": "Steam Aile Paylaşımı"}
]

USER_CARTS = {}
USER_ORDERS = {}

USERS = {
    "admin@interform.inc": {
        "password": "admin123",
        "role": "Administrator",
        "name": "Sistem Admin"
    }
}

# --- ANA SAYFA (GİRİŞ / KAYIT) ---
@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return """
    <html>
        <head>
            <title>Interform Inc. | Steam Lisans ve Yönetim Paneli</title>
            <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@400;600&display=swap" rel="stylesheet">
            <style>
                body { background: #070707; color: #fff; font-family: 'Rajdhani', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                .auth-box { background: #111; border: 1px solid #262626; padding: 40px; width: 400px; box-shadow: 0 0 20px rgba(0,0,0,0.8); }
                h1 { font-family: 'Orbitron'; color: #3a86ff; font-size: 1.5rem; text-align: center; margin-bottom: 25px; }
                input { width: 100%; padding: 12px; margin-top: 10px; background: #000; border: 1px solid #262626; color: #fff; font-family: inherit; }
                .btn { background: #3a86ff; color: #fff; border: none; padding: 12px; margin-top: 20px; width: 100%; font-family: 'Orbitron'; font-weight: bold; cursor: pointer; }
                .btn:hover { background: #2670e8; }
                .toggle-link { text-align: center; margin-top: 15px; font-size: 0.9rem; color: #888; cursor: pointer; }
                .toggle-link span { color: #3a86ff; text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="auth-box">
                <h1 id="formTitle">// GİRİŞ YAP</h1>
                <div id="errorMsg" style="color:#ff5555; font-size:0.9rem; margin-bottom:10px; display:none;"></div>
                
                <div id="nameField" style="display:none;">
                    <input type="text" id="name" placeholder="Ad Soyad / Şirket Unvanı">
                </div>
                <input type="email" id="email" placeholder="E-posta Adresi">
                <input type="password" id="password" placeholder="Şifre">
                
                <button class="btn" id="submitBtn" onclick="handleAuth()">SİSTEME BAĞLAN</button>
                <div class="toggle-link" onclick="toggleMode()"><span id="toggleText">Hesabınız yok mu? Kayıt olun.</span></div>
            </div>

            <script>
                let isRegister = false;
                function toggleMode() {
                    isRegister = !isRegister;
                    document.getElementById('formTitle').innerText = isRegister ? "// YENİ HESAP OLUŞTUR" : "// GİRİŞ YAP";
                    document.getElementById('nameField').style.display = isRegister ? "block" : "none";
                    document.getElementById('submitBtn').innerText = isRegister ? "KAYIT OL VE BAŞLA" : "SİSTEME BAĞLAN";
                    document.getElementById('toggleText').innerText = isRegister ? "Zaten hesabınız var mı? Giriş yapın." : "Hesabınız yok mu? Kayıt olun.";
                }

                async function handleAuth() {
                    const email = document.getElementById('email').value.trim().toLowerCase();
                    const password = document.getElementById('password').value;
                    const name = document.getElementById('name').value;
                    const errorBox = document.getElementById('errorMsg');
                    errorBox.style.display = 'none';

                    const endpoint = isRegister ? '/api/register' : '/api/login';
                    const payload = isRegister ? {email, password, name} : {email, password};

                    const res = await fetch(endpoint, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(payload)
                    });
                    const data = await res.json();

                    if(res.ok) {
                        if(isRegister) {
                            alert(data.message);
                            toggleMode();
                        } else {
                            localStorage.setItem('userEmail', data.email);
                            window.location.href = data.redirect;
                        }
                    } else {
                        errorBox.innerText = data.detail || "Bir hata oluştu.";
                        errorBox.style.display = 'block';
                    }
                }
            </script>
        </body>
    </html>
    """

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

    USERS[email] = {"password": password, "role": "Üye", "name": name}
    return {"status": "success", "message": "Kayıt başarılı. Giriş yapabilirsiniz."}

@app.post("/api/login")
async def api_login(request: Request):
    data = await request.json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = USERS.get(email)
    if not user or user["password"] != password:
        raise HTTPException(status_code=400, detail="Geçersiz e-posta veya şifre.")

    if user["role"] in ["Administrator", "Yönetim Kurulu", "BT Genel Sorumlu", "Mağaza Genel Sorumlu", "Mağaza Yetkilisi", "BT Yetkilisi", "Genel Yetkili", "Yetkili"]:
        redirect_url = "/admin-dashboard"
    else:
        redirect_url = "/store"

    return {"status": "success", "role": user["role"], "redirect": redirect_url, "email": email}

# --- MAĞAZA VE SEPET API'LERİ ---
@app.get("/api/steam-accounts")
async def get_steam_accounts():
    return {"accounts": STEAM_ACCOUNTS}

@app.post("/api/cart/add")
async def add_to_cart(request: Request):
    data = await request.json()
    email = data.get("email", "guest@interform.inc").strip().lower()
    game_id = data.get("id")

    game = next((g for g in STEAM_ACCOUNTS if g["id"] == game_id), None)
    if not game:
        raise HTTPException(status_code=404, detail="Oyun bulunamadı.")
    if game["stock"] <= 0:
        raise HTTPException(status_code=400, detail="Üzgünüz, bu oyunun stokları tükendi.")

    if email not in USER_CARTS:
        USER_CARTS[email] = []

    USER_CARTS[email].append(game)
    return {"status": "success", "message": f"{game['name']} sepete eklendi."}

@app.get("/api/cart/{email}")
async def get_cart(email: str):
    email = email.strip().lower()
    items = USER_CARTS.get(email, [])
    total = sum(item["price"] for item in items)
    orders = USER_ORDERS.get(email, [])
    return {"items": items, "total": round(total, 2), "orders": orders}

@app.post("/api/checkout")
async def checkout(request: Request):
    data = await request.json()
    email = data.get("email", "guest@interform.inc").strip().lower()
    card_number = data.get("card_number", "").strip()
    card_expiry = data.get("card_expiry", "").strip()
    card_cvv = data.get("card_cvv", "").strip()

    if not card_number or not card_expiry or not card_cvv:
        raise HTTPException(status_code=400, detail="Lütfen tüm kart bilgilerini eksiksiz doldurun.")
    
    if len(card_number) < 16:
        raise HTTPException(status_code=400, detail="Geçersiz kart numarası.")

    cart_items = USER_CARTS.get(email, [])
    if not cart_items:
        raise HTTPException(status_code=400, detail="Sepetiniz boş.")

    purchased_licenses = []
    for item in cart_items:
        game = next((g for g in STEAM_ACCOUNTS if g["id"] == item["id"]), None)
        if game and game["stock"] > 0:
            game["stock"] -= 1
            import uuid
            license_key = f"STEAM-FAM-{str(uuid.uuid4()).upper()[:16]}"
            purchased_licenses.append({
                "game_name": game["name"],
                "key": license_key,
                "status": "Aktif / Ödeme Onaylandı"
            })

    if email not in USER_ORDERS:
        USER_ORDERS[email] = []
    USER_ORDERS[email].extend(purchased_licenses)
    
    USER_CARTS[email] = []
    
    return {
        "status": "success", 
        "message": "Ödemeniz başarıyla tahsil edildi! Lisans anahtarlarınız oluşturuldu."
    }

# --- ADMIN API'LERİ ---
@app.post("/api/admin/add-steam-account")
async def add_steam_account(request: Request):
    data = await request.json()
    new_id = len(STEAM_ACCOUNTS) + 1
    STEAM_ACCOUNTS.append({
        "id": new_id,
        "name": data.get("name"),
        "price": float(data.get("price", 0)),
        "category": data.get("category", "AAA Oyun"),
        "stock": int(data.get("stock", 5)),
        "type": "Steam Aile Paylaşımı (Güvenli Kilitli)"
    })
    return {"status": "success", "message": "Steam aile hesabı envantere başarıyla eklendi."}

@app.post("/api/admin/update-rank")
async def update_rank(request: Request):
    data = await request.json()
    email = data.get("email", "").strip().lower()
    rank = data.get("rank")
    admin_secret = data.get("adminSecret", "")

    if rank == "Administrator" and admin_secret != "admin123":
        raise HTTPException(status_code=403, detail="Administrator yetkisi için doğru admin şifresi gerekli.")

    if email in USERS:
        USERS[email]["role"] = rank
        return {"status": "success", "message": f"{email} kullanıcısının rütbesi başarıyla {rank} olarak güncellendi."}
    raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

@app.get("/api/admin/system-analysis")
async def get_system_analysis():
    total_stock = sum(acc["stock"] for acc in STEAM_ACCOUNTS)
    total_users = len(USERS)
    return {
        "cpu_usage": SYSTEM_STATE["cpu"],
        "ram_usage": SYSTEM_STATE["ram"],
        "disk_io": "0.8 MB/s",
        "active_threads": 42,
        "database_status": SYSTEM_STATE["status"],
        "security_threats": SYSTEM_STATE["active_threats"],
        "total_stock": total_stock,
        "total_users": total_users
    }

@app.post("/api/admin/inject-fault")
async def inject_fault():
    SYSTEM_STATE["status"] = "KRİTİK UYARI (Hesap Havuzu Senkronizasyon Hatası)"
    SYSTEM_STATE["cpu"] = "%88.5 (Aşırı İstek)"
    SYSTEM_STATE["active_threats"] = 1
    SYSTEM_STATE["memory_leak_simulated"] = True
    return {"status": "success", "message": "Simüle edilmiş hata sisteme enjekte edildi."}

@app.post("/api/ai-query")
async def ai_query(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "").lower()
    
    action_taken = ""
    if "onar" in prompt or "fix" in prompt or "çöz" in prompt or "optimize" in prompt:
        SYSTEM_STATE["status"] = "STABİL"
        SYSTEM_STATE["cpu"] = "14.2%"
        SYSTEM_STATE["ram"] = "3.8 GB / 16 GB"
        SYSTEM_STATE["active_threats"] = 0
        SYSTEM_STATE["memory_leak_simulated"] = False
        action_taken = "\n\n[OTONOM İŞLEM BAŞARILI]: AI çekirdeği veritabanını senkronize etti ve sistemi stabil hale getirdi."

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {"response": f"[SİSTEM UYARISI]: GROQ_API_KEY bulunamadı! Simüle Edilen AI Yanıtı: İşlem başarıyla tamamlandı.{action_taken}"}
    
    try:
        client = Groq(api_key=api_key)
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Sen Interform Inc.'in tam yetkili, otonom başmühendisisin."},
                {"role": "user", "content": data.get("prompt", "")}
            ],
            model="qwen/qwen3.8-27b",
        )
        return {"response": chat_completion.choices[0].message.content + action_taken}
    except Exception as e:
        return {"response": f"AI Servis Hatası: {str(e)}{action_taken}"}

# --- MAĞAZA SAYFASI ---
@app.get("/store", response_class=HTMLResponse)
async def store_page():
    return """
    <html>
        <head>
            <title>Interform Inc. | Steam Aile Paylaşımı Mağazası</title>
            <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@400;600&display=swap" rel="stylesheet">
            <style>
                body { background: #070707; color: #fff; font-family: 'Rajdhani', sans-serif; padding: 40px; }
                .container { max-width: 1200px; margin: 0 auto; }
                .header-flex { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #262626; padding-bottom: 20px; }
                .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-top: 30px; }
                .card { background: #111; border: 1px solid #262626; padding: 25px; position: relative; }
                .badge-family { position: absolute; top: 20px; right: 20px; background: rgba(58,134,255,0.15); border: 1px solid #3a86ff; color: #3a86ff; padding: 4px 10px; font-size: 0.7rem; font-family: 'Orbitron'; }
                .btn { background: #3a86ff; color: #fff; border: none; padding: 12px 15px; font-family: 'Orbitron'; cursor: pointer; margin-top: 15px; width: 100%; font-weight: bold; }
                .btn:hover { background: #2670e8; }
                .cart-box { background: #111; border: 1px solid #3a86ff; padding: 25px; margin-top: 40px; }
                .warning-note { background: #1a1a1a; border-left: 3px solid #ffaa00; padding: 15px; margin-top: 20px; font-size: 0.95rem; color: #ccc; }
                .nav-link { color: #aaa; text-decoration: none; margin-left: 15px; font-family: 'Orbitron'; font-size: 0.8rem; }
                .license-box { background: #0b1a10; border: 1px solid #4caf7d; padding: 20px; margin-top: 40px; }
                
                /* Modal Pencere Tasarımı */
                .modal { display: none; position: fixed; z-index: 100; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.8); justify-content: center; align-items: center; }
                .modal-content { background: #111; border: 1px solid #3a86ff; padding: 30px; width: 400px; box-shadow: 0 0 30px rgba(58,134,255,0.3); }
                .modal input { width: 100%; padding: 10px; margin-top: 10px; background: #000; border: 1px solid #333; color: #fff; font-family: inherit; }
                .row { display: flex; gap: 10px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header-flex">
                    <h1 style="font-family:'Orbitron'; color:#3a86ff; font-size:1.4rem;">// STEAM AİLE PAYLAŞIMI MAĞAZASI</h1>
                    <div>
                        <span id="userDisplay" style="color:#aaa; font-size:0.9rem; margin-right:15px;"></span>
                        <a href="/admin-dashboard" class="nav-link">YÖNETİM PANELİ</a>
                        <a href="/" class="nav-link" style="color:#ff5555;">ÇIKIŞ</a>
                    </div>
                </div>
                
                <div class="warning-note">
                    <b>⚠️ Güvenlik Protokolü:</b> Tüm hesaplar Steam Aile Paylaşımı (Family Sharing) ile verilir. Ödeme aşamasında kart bilgileriniz şifrelenerek işlenir.
                </div>

                <div class="grid" id="steamGrid"></div>

                <div class="cart-box">
                    <h2 style="font-family:'Orbitron'; color:#3a86ff; font-size:1.2rem;">🛍️ SEPETİNİZ VE ÖDEME</h2>
                    <div id="cartItems" style="margin-top:15px; color:#aaa;">Sepetiniz henüz boş.</div>
                    <div id="cartTotal" style="font-family:'Orbitron'; font-size:1.2rem; margin-top:15px; color:#4caf7d;"></div>
                    <button class="btn" id="checkoutBtn" style="display:none; background:#4caf7d;" onclick="openCheckoutModal()">GÜVENLİ ÖDEME EKRANINI AÇ</button>
                </div>

                <div class="license-box" id="licenseSection" style="display:none;">
                    <h2 style="font-family:'Orbitron'; color:#4caf7d; font-size:1.2rem;">🔑 SATIN ALINAN LİSANS ANAHTARLARINIZ</h2>
                    <div id="licenseList" style="margin-top:15px;"></div>
                </div>
            </div>

            <!-- ÖDEME MODALI -->
            <div id="checkoutModal" class="modal">
                <div class="modal-content">
                    <h2 style="font-family:'Orbitron'; color:#3a86ff; font-size:1.1rem; margin-bottom:15px;">💳 KREDİ KARTI İLE ÖDEME</h2>
                    <div id="modalError" style="color:#ff5555; font-size:0.85rem; margin-bottom:10px; display:none;"></div>
                    <input type="text" id="cardNumber" placeholder="Kart Numarası (örn: 4532 ... ... ...)" maxlength="16">
                    <div class="row">
                        <input type="text" id="cardExpiry" placeholder="AA/YY" maxlength="5">
                        <input type="password" id="cardCvv" placeholder="CVV" maxlength="3">
                    </div>
                    <button class="btn" style="background:#4caf7d; margin-top:20px;" onclick="processCheckout()">ÖDEMEYİ ONAYLA VE TAMAMLA</button>
                    <button class="btn" style="background:#333; margin-top:10px;" onclick="closeCheckoutModal()">İPTAL</button>
                </div>
            </div>

            <script>
                const userEmail = localStorage.getItem('userEmail') || "guest@interform.inc";
                document.getElementById('userDisplay').innerText = `Kullanıcı: ${userEmail}`;

                async function loadStore() {
                    const res = await fetch('/api/steam-accounts');
                    const data = await res.json();
                    const grid = document.getElementById('steamGrid');
                    grid.innerHTML = '';
                    data.accounts.forEach(acc => {
                        grid.innerHTML += `
                            <div class="card">
                                <div class="badge-family">AİLE PAYLAŞIMI</div>
                                <h3 style="font-family:'Orbitron'; font-size: 1.2rem;">${acc.name}</h3>
                                <p style="color:#aaa; margin-top:5px;">Kategori: ${acc.category}</p>
                                <p style="color:#4caf7d; font-size:1.4rem; font-weight:bold; margin-top:10px;">$${acc.price}</p>
                                <p style="color:#888; font-size:0.9rem;">Mevcut Stok: ${acc.stock} Slot</p>
                                <button class="btn" onclick="addToCart(${acc.id})" ${acc.stock <= 0 ? 'disabled style="background:#444;cursor:not-allowed;"' : ''}>${acc.stock > 0 ? 'SEPETE EKLE' : 'STOK TÜKENDİ'}</button>
                            </div>
                        `;
                    });
                    loadCart();
                }

                async function addToCart(id) {
                    const res = await fetch('/api/cart/add', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({id: id, email: userEmail})
                    });
                    const data = await res.json();
                    if(res.ok) {
                        loadStore();
                    } else {
                        alert(data.detail);
                    }
                }

                async function loadCart() {
                    const res = await fetch(`/api/cart/${userEmail}`);
                    const data = await res.json();
                    const cartDiv = document.getElementById('cartItems');
                    const totalDiv = document.getElementById('cartTotal');
                    const checkoutBtn = document.getElementById('checkoutBtn');
                    const licenseSection = document.getElementById('licenseSection');
                    const licenseList = document.getElementById('licenseList');

                    if(data.items.length === 0) {
                        cartDiv.innerHTML = "Sepetiniz boş.";
                        totalDiv.innerHTML = "";
                        checkoutBtn.style.display = "none";
                    } else {
                        cartDiv.innerHTML = data.items.map(i => `<div style="padding:8px 0; border-bottom:1px solid #222; display:flex; justify-content:space-between;"><span>${i.name}</span><span>$${i.price}</span></div>`).join('');
                        totalDiv.innerHTML = `Toplam Tutar: $${data.total}`;
                        checkoutBtn.style.display = "block";
                    }

                    if(data.orders && data.orders.length > 0) {
                        licenseSection.style.display = "block";
                        licenseList.innerHTML = data.orders.map(o => `
                            <div style="background:#051109; border:1px solid #2d6a4f; padding:12px; margin-top:10px;">
                                <div style="font-weight:bold; color:#fff;">${o.game_name}</div>
                                <div style="font-family:monospace; color:#4caf7d; margin-top:5px; font-size:1.1rem;">Anahtar: ${o.key}</div>
                                <div style="font-size:0.8rem; color:#888; margin-top:3px;">Durum: ${o.status}</div>
                            </div>
                        `).join('');
                    }
                }

                function openCheckoutModal() {
                    document.getElementById('checkoutModal').style.display = 'flex';
                }

                function closeCheckoutModal() {
                    document.getElementById('checkoutModal').style.display = 'none';
                }

                async function processCheckout() {
                    const card_number = document.getElementById('cardNumber').value;
                    const card_expiry = document.getElementById('cardExpiry').value;
                    const card_cvv = document.getElementById('cardCvv').value;
                    const errorBox = document.getElementById('modalError');
                    errorBox.style.display = 'none';

                    const res = await fetch('/api/checkout', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({email: userEmail, card_number, card_expiry, card_cvv})
                    });
                    const data = await res.json();
                    
                    if(res.ok) {
                        alert(data.message);
                        closeCheckoutModal();
                        loadStore();
                    } else {
                        errorBox.innerText = data.detail;
                        errorBox.style.display = 'block';
                    }
                }

                loadStore();
            </script>
        </body>
    </html>
    """

# --- YÖNETİCİ PANELİ ---
@app.get("/admin-dashboard", response_class=HTMLResponse)
async def admin_dashboard():
    return """
    <html>
        <head>
            <title>Interform | Otonom Yönetici Paneli</title>
            <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=Rajdhani:wght@400;500;600;700&display=swap" rel="stylesheet">
            <style>
                :root {
                    --bg: #070707; --surface: #111111; --surface-light: #1a1a1a;
                    --border: #262626; --primary: #ffffff; --secondary: #999999;
                    --accent: #3a86ff; --success: #4caf7d; --warning: #ffaa00;
                }
                * { margin:0; padding:0; box-sizing:border-box; }
                body { background: var(--bg); color: var(--primary); font-family: 'Rajdhani', sans-serif; padding: 30px; min-height: 100vh; }
                .admin-container { max-width: 1400px; margin: 0 auto; display: flex; flex-direction: column; gap: 25px; }
                
                .admin-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 20px; }
                .admin-logo { font-family: 'Orbitron', monospace; font-size: 1.3rem; font-weight: 900; letter-spacing: 0.2em; color: var(--primary); }
                .admin-logo span { color: var(--accent); }
                .admin-nav { display: flex; gap: 15px; align-items: center; }
                .badge { background: rgba(58,134,255,0.1); border: 1px solid var(--accent); color: var(--accent); padding: 6px 14px; font-family: 'Orbitron', monospace; font-size: 0.7rem; }
                .logout-btn { border: 1px solid var(--border); background: var(--surface); color: var(--secondary); padding: 8px 18px; font-family: 'Orbitron', monospace; font-size: 0.75rem; text-decoration: none; }
                
                .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
                .stat-box { background: var(--surface); border: 1px solid var(--border); padding: 20px; }
                .stat-title { font-family: 'Orbitron', monospace; font-size: 0.7rem; color: var(--secondary); margin-bottom: 8px; }
                .stat-value { font-family: 'Orbitron', monospace; font-size: 1.4rem; font-weight: 700; color: var(--primary); }
                .stat-value.green { color: var(--success); }
                .stat-value.warning { color: var(--warning); }

                .analysis-section { background: var(--surface); border: 1px solid var(--border); padding: 25px; }
                .analysis-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top: 15px; }
                .analysis-card { background: var(--bg); border: 1px solid var(--border); padding: 15px; }
                .analysis-label { font-size: 0.8rem; color: var(--secondary); font-family: 'Orbitron', monospace; }
                .analysis-val { font-size: 1.2rem; font-weight: 700; color: var(--warning); margin-top: 5px; font-family: 'Orbitron', monospace; }
                .action-bar { margin-top: 15px; display: flex; gap: 10px; flex-wrap: wrap; }
                .sys-btn { background: var(--surface-light); border: 1px solid var(--border); color: #fff; padding: 8px 15px; font-family: 'Orbitron'; font-size: 0.75rem; cursor: pointer; }
                .sys-btn.danger { border-color: rgba(255,0,127,0.4); color: #ff007f; }

                .workspace-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 25px; }
                .panel-card { background: var(--surface); border: 1px solid var(--border); padding: 25px; display: flex; flex-direction: column; height: 480px; }
                .panel-title { font-family: 'Orbitron', monospace; font-size: 0.95rem; font-weight: 700; color: var(--accent); margin-bottom: 15px; }

                .ai-chat-box { flex: 1; background: var(--bg); border: 1px solid var(--border); padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; margin-bottom: 12px; }
                .ai-msg { padding: 10px 14px; border-radius: 2px; max-width: 85%; line-height: 1.5; white-space: pre-wrap; }
                .ai-msg.system { background: var(--surface-light); border-left: 3px solid var(--accent); align-self: flex-start; }
                .ai-msg.user { background: rgba(58,134,255,0.15); border-right: 3px solid var(--accent); align-self: flex-end; }
                
                .ai-input-group { display: flex; gap: 10px; }
                .ai-input { flex: 1; background: var(--bg); border: 1px solid var(--border); padding: 10px; color: var(--primary); font-family: inherit; outline: none; }
                .ai-btn { background: var(--accent); color: #fff; border: none; padding: 0 18px; font-family: 'Orbitron', monospace; font-weight: bold; cursor: pointer; }

                .logs-container { flex: 1; background: var(--bg); border: 1px solid var(--border); padding: 15px; overflow-y: auto; font-family: 'Courier New', monospace; font-size: 0.8rem; color: #00ff66; display: flex; flex-direction: column; gap: 6px; }
                
                .mgmt-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 25px; }
                .mgmt-box { background: var(--surface); border: 1px solid var(--border); padding: 25px; }
                input, select { padding: 10px; margin-top: 8px; width: 100%; background: var(--bg); color: #fff; border: 1px solid var(--border); font-family: inherit; }
                .mgmt-btn { background: #3a86ff; color: #fff; border: none; padding: 10px; margin-top: 10px; width: 100%; font-family: 'Orbitron', monospace; font-weight: bold; cursor: pointer; }
            </style>
        </head>
        <body>
            <div class="admin-container">
                <div class="admin-header">
                    <div class="admin-logo">INTERFORM<span>.INC</span> // YÖNETİCİ KONTROL MERKEZİ</div>
                    <div class="admin-nav">
                        <div class="badge">SELF-HEALING AI AKTİF</div>
                        <a href="/store" class="logout-btn">STEAM MAĞAZA</a>
                        <a href="/" class="logout-btn">ÇIKIŞ</a>
                    </div>
                </div>

                <div class="stats-grid">
                    <div class="stat-box">
                        <div class="stat-title">SİSTEM DURUMU</div>
                        <div class="stat-value green" id="statStatus">STABİL</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-title">KAYITLI KULLANICI</div>
                        <div class="stat-value" id="statUsers" style="color:var(--accent);">Yükleniyor...</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-title">KALAN STOK (SLOT)</div>
                        <div class="stat-value" id="statStock">Yükleniyor...</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-title">GÜVENLİK DUVARI</div>
                        <div class="stat-value green" id="statThreats">AKTİF (0 Tehdit)</div>
                    </div>
                </div>

                <div class="analysis-section">
                    <div class="panel-title" style="margin-bottom: 5px;">📊 CANLI SİSTEM ANALİZİ & OTONOM ONARIM</div>
                    <div class="analysis-grid">
                        <div class="analysis-card"><div class="analysis-label">CPU KULLANIMI</div><div class="analysis-val" id="cpuVal">Yükleniyor...</div></div>
                        <div class="analysis-card"><div class="analysis-label">RAM TÜKETİMİ</div><div class="analysis-val" id="ramVal" style="color:#3a86ff;">Yükleniyor...</div></div>
                        <div class="analysis-card"><div class="analysis-label">DİSK I/O</div><div class="analysis-val" id="diskVal" style="color:#00ff66;">Yükleniyor...</div></div>
                        <div class="analysis-card"><div class="analysis-label">AKTİF THREADLER</div><div class="analysis-val" id="threadVal">Yükleniyor...</div></div>
                    </div>
                    <div class="action-bar">
                        <button class="sys-btn" onclick="fetchSystemAnalysis()">🔄 METRİKLERİ YENİLE</button>
                        <button class="sys-btn danger" onclick="injectFault()">⚠️ SİSTEME HATA ENJEKTE ET (TEST)</button>
                        <button class="sys-btn" style="border-color:#3a86ff; color:#3a86ff;" onclick="askAiToHeal()">🤖 AI OTONOM ONARIM BAŞLAT</button>
                    </div>
                </div>

                <div class="workspace-grid">
                    <div class="panel-card">
                        <div class="panel-title">🤖 TAM YETKİLİ YAPAY ZEKA ASİSTANI</div>
                        <div class="ai-chat-box" id="chatBox">
                            <div class="ai-msg system">Otonom AI Başmühendis hazır. "Sistemi tara ve onar" diyerek hesap havuzunu optimize edebilirsiniz.</div>
                        </div>
                        <div class="ai-input-group">
                            <input type="text" id="aiPrompt" class="ai-input" placeholder="AI'ya komut ver..." onkeypress="checkEnter(event)">
                            <button class="ai-btn" onclick="sendAiQuery()">ÇALIŞTIR</button>
                        </div>
                    </div>

                    <div class="panel-card">
                        <div class="panel-title">🛡️ CANLI SİSTEM LOGLARI</div>
                        <div class="logs-container" id="logsContainer">
                            <div class="log-line">[22:00:01] [INFO] FastAPI sunucu başarıyla başlatıldı.</div>
                            <div class="log-line">[22:00:05] [AUTH] admin@interform.inc root yetkisiyle bağlandı.</div>
                            <div class="log-line">[22:00:20] [SECURITY] E-posta/Şifre koruma kilidi aktif.</div>
                        </div>
                    </div>
                </div>

                <div class="mgmt-grid">
                    <div class="mgmt-box">
                        <h3 style="font-family:'Orbitron'; color:var(--accent); font-size: 0.9rem;">📦 YENİ STEAM HESABI EKLE</h3>
                        <input type="text" id="sName" placeholder="Oyun Adı (örn: RDR2 Aile Hesabı)">
                        <input type="number" id="sPrice" placeholder="Fiyat ($)">
                        <input type="text" id="sCategory" placeholder="Kategori">
                        <input type="number" id="sStock" placeholder="Stok Adedi">
                        <button class="mgmt-btn" onclick="addSteamAccount()">STEAM HESABINI KAYDET</button>
                    </div>

                    <div class="mgmt-box">
                        <h3 style="font-family:'Orbitron'; color:#3a86ff; font-size: 0.9rem;">🛡️ RÜTBE ATAMA YÖNETİMİ</h3>
                        <input type="text" id="targetEmail" placeholder="Kullanıcı E-postası">
                        <select id="targetRank">
                            <option value="Administrator">Administrator</option>
                            <option value="Yönetim Kurulu">Yönetim Kurulu</option>
                            <option value="Mağaza Yetkilisi">Mağaza Yetkilisi</option>
                            <option value="Üye">Üye</option>
                        </select>
                        <input type="password" id="adminSecret" placeholder="Admin Şifresi (Sadece Admin için)">
                        <button class="mgmt-btn" onclick="updateRank()">RÜTKEYİ GÜNCELLE</button>
                    </div>
                </div>
            </div>

            <script>
                async function fetchSystemAnalysis() {
                    const res = await fetch('/api/admin/system-analysis');
                    const data = await res.json();
                    document.getElementById('cpuVal').innerText = data.cpu_usage;
                    document.getElementById('ramVal').innerText = data.ram_usage;
                    document.getElementById('diskVal').innerText = data.disk_io;
                    document.getElementById('threadVal').innerText = data.active_threads + " Aktif";
                    
                    document.getElementById('statUsers').innerText = data.total_users + " Kullanıcı";
                    document.getElementById('statStock').innerText = data.total_stock + " Slot";

                    const statStatus = document.getElementById('statStatus');
                    statStatus.innerText = data.database_status;
                    statStatus.className = data.database_status.includes("KRİTİK") ? "stat-value warning" : "stat-value green";

                    const statThreats = document.getElementById('statThreats');
                    statThreats.innerText = data.security_threats > 0 ? `ALARM (${data.security_threats} Tehdit)` : "AKTİF (0 Tehdit)";
                    statThreats.className = data.security_threats > 0 ? "stat-value warning" : "stat-value green";
                }
                fetchSystemAnalysis();
                setInterval(fetchSystemAnalysis, 5000);

                async function injectFault() {
                    const res = await fetch('/api/admin/inject-fault', { method: 'POST' });
                    const data = await res.json();
                    alert(data.message);
                    document.getElementById('logsContainer').innerHTML += `<div class="log-line" style="color:#ffaa00;">[WARNING] Hesap senkronizasyon hatası enjekte edildi!</div>`;
                    fetchSystemAnalysis();
                }

                function askAiToHeal() {
                    document.getElementById('aiPrompt').value = "Sistemi tara ve tespit edilen hataları onar.";
                    sendAiQuery();
                }

                async function sendAiQuery() {
                    const inputField = document.getElementById('aiPrompt');
                    const chatBox = document.getElementById('chatBox');
                    const prompt = inputField.value.trim();
                    if(!prompt) return;

                    chatBox.innerHTML += `<div class="ai-msg user">${prompt}</div>`;
                    inputField.value = '';

                    const res = await fetch('/api/ai-query', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ prompt })
                    });
                    const data = await res.json();
                    chatBox.innerHTML += `<div class="ai-msg system">${data.response}</div>`;
                    chatBox.scrollTop = chatBox.scrollHeight;
                    fetchSystemAnalysis();
                }

                function checkEnter(e) { if (e.key === 'Enter') { sendAiQuery(); } }

                async function addSteamAccount() {
                    const name = document.getElementById('sName').value;
                    const price = document.getElementById('sPrice').value;
                    const category = document.getElementById('sCategory').value;
                    const stock = document.getElementById('sStock').value;
                    
                    const res = await fetch('/api/admin/add-steam-account', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({name, price, category, stock})
                    });
                    const data = await res.json();
                    alert(data.message);
                    fetchSystemAnalysis();
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
                    alert(res.ok ? data.message : "Hata: " + data.detail);
                }
            </script>
        </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
