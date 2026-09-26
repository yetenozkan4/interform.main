from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from groq import Groq

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# --- VERİTABANI / BELLEK SİMÜLASYONU ---
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

USERS = {
    "admin@interform.inc": {
        "password": "admin123",
        "role": "Administrator",
        "name": "Sistem Admin"
    }
}

PRODUCTS = [
    {"id": 1, "name": "Cyberpunk Neural Link v1", "price": 299.99, "category": "Donanım", "stock": 14},
    {"id": 2, "name": "Quantum Encryption Key", "price": 149.50, "category": "Yazılım", "stock": 42},
    {"id": 3, "name": "AI Sentinel Core", "price": 599.00, "category": "AI Modülü", "stock": 5}
]

# --- ANA SAYFA ---
@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})

# --- KAYIT & GİRİŞ ---
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

    if user["role"] == "Administrator" or "Yönetim" in user["role"] or "Sorumlu" in user["role"] or "Yetkili" in user["role"]:
        redirect_url = "/admin-dashboard"
    else:
        redirect_url = "/dashboard"

    return {"status": "success", "role": user["role"], "redirect": redirect_url, "email": email}

# --- YÖNETİM ENDPOINTLERİ ---
@app.post("/api/admin/update-rank")
async def update_user_rank(request: Request):
    data = await request.json()
    target_email = data.get("email", "").strip().lower()
    new_rank = data.get("rank", "")
    admin_secret = data.get("adminSecret", "")

    if new_rank not in RANKS:
        raise HTTPException(status_code=400, detail="Geçersiz rütbe.")
    if new_rank == "Administrator" and admin_secret != "admin123":
        raise HTTPException(status_code=403, detail="Administrator rütbesi için doğru admin şifresi gerekli!")
    if target_email not in USERS:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    USERS[target_email]["role"] = new_rank
    return {"status": "success", "message": f"{target_email} rütbesi {new_rank} yapıldı."}

@app.post("/api/admin/add-product")
async def add_product(request: Request):
    data = await request.json()
    new_id = len(PRODUCTS) + 1
    PRODUCTS.append({
        "id": new_id,
        "name": data.get("name"),
        "price": float(data.get("price", 0)),
        "category": data.get("category", "Genel"),
        "stock": int(data.get("stock", 10))
    })
    return {"status": "success", "message": "Ürün mağazaya eklendi."}

@app.get("/api/products")
async def get_products():
    return {"products": PRODUCTS}

# --- SİSTEM ANALİZİ API (ÖZEL) ---
@app.get("/api/admin/system-analysis")
async def get_system_analysis():
    # Gerçek zamanlı sistem analizi verileri simülasyonu
    return {
        "cpu_usage": "18.4%",
        "ram_usage": "4.2 GB / 16 GB (%26.2)",
        "disk_io": "1.2 MB/s",
        "active_threads": 48,
        "network_traffic": "450 KB/s",
        "database_status": "Healthy (Latency: 2ms)",
        "security_threats": 0,
        "ai_status": "Active (Qwen-3.8-27b Ready)"
    }

# --- TAM YETKİLİ YAPAY ZEKA ENDPOINTİ ---
@app.post("/api/ai-query")
async def ai_query(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {"response": "[SİSTEM UYARISI]: GROQ_API_KEY bulunamadı! Simüle Edilen AI Analizi: Altyapı kararlı, CPU %18 seviyesinde seyrediyor, herhangi bir güvenlik açığı tespit edilmedi."}
    
    try:
        client = Groq(api_key=api_key)
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Sen Interform Inc.'in tam yetkili kurumsal operasyonel yapay zeka asistanısın ve sistem analistisin. Admin paneli için derinlemesine sistem analizi, güvenlik denetim raporları, sunucu optimizasyon tavsiyeleri ve teknik destek sağlıyorsun. Profesyonel, siberpunk ve üst düzey yetkili bir üslubun var."
                },
                {"role": "user", "content": prompt}
            ],
            model="qwen/qwen3.8-27b",
        )
        return {"response": chat_completion.choices[0].message.content}
    except Exception as e:
        return {"response": f"AI Servis Hatası: {str(e)}"}

# --- MAĞAZA SAYFASI ---
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
            </script>
        </body>
    </html>
    """

# --- KULLANICI PANELİ ---
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

# --- GELİŞMİŞ YÖNETİCİ PANELİ (Sistem Analizi, Loglar, Rütbe & Ürün Yönetimi) ---
@app.get("/admin-dashboard", response_class=HTMLResponse)
async def admin_dashboard():
    return """
    <html>
        <head>
            <title>Interform | Gelişmiş Yönetici Paneli & Sistem Analizi</title>
            <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=Rajdhani:wght@400;500;600;700&display=swap" rel="stylesheet">
            <style>
                :root {
                    --bg: #070707;
                    --surface: #111111;
                    --surface-light: #1a1a1a;
                    --border: #262626;
                    --primary: #ffffff;
                    --secondary: #999999;
                    --accent: #ff007f;
                    --success: #4caf7d;
                    --warning: #ffaa00;
                }
                * { margin:0; padding:0; box-sizing:border-box; }
                body { background: var(--bg); color: var(--primary); font-family: 'Rajdhani', sans-serif; padding: 30px; min-height: 100vh; }
                .admin-container { max-width: 1400px; margin: 0 auto; display: flex; flex-direction: column; gap: 25px; }
                
                .admin-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 20px; }
                .admin-logo { font-family: 'Orbitron', monospace; font-size: 1.3rem; font-weight: 900; letter-spacing: 0.2em; color: var(--primary); }
                .admin-logo span { color: var(--accent); }
                .admin-nav { display: flex; gap: 15px; align-items: center; }
                .badge { background: rgba(255,0,127,0.1); border: 1px solid var(--accent); color: var(--accent); padding: 6px 14px; font-family: 'Orbitron', monospace; font-size: 0.7rem; letter-spacing: 0.1em; }
                .logout-btn { border: 1px solid var(--border); background: var(--surface); color: var(--secondary); padding: 8px 18px; font-family: 'Orbitron', monospace; font-size: 0.75rem; text-decoration: none; transition: 0.2s; }
                .logout-btn:hover { border-color: var(--primary); color: var(--primary); }

                .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
                .stat-box { background: var(--surface); border: 1px solid var(--border); padding: 20px; }
                .stat-title { font-family: 'Orbitron', monospace; font-size: 0.7rem; color: var(--secondary); letter-spacing: 0.15em; margin-bottom: 8px; }
                .stat-value { font-family: 'Orbitron', monospace; font-size: 1.5rem; font-weight: 700; color: var(--primary); }
                .stat-value.green { color: var(--success); }

                /* Sistem Analizi Bölümü */
                .analysis-section { background: var(--surface); border: 1px solid var(--border); padding: 25px; }
                .analysis-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top: 15px; }
                .analysis-card { background: var(--bg); border: 1px solid var(--border); padding: 15px; }
                .analysis-label { font-size: 0.8rem; color: var(--secondary); font-family: 'Orbitron', monospace; }
                .analysis-val { font-size: 1.2rem; font-weight: 700; color: var(--warning); margin-top: 5px; font-family: 'Orbitron', monospace; }
                .action-bar { margin-top: 15px; display: flex; gap: 10px; }
                .sys-btn { background: var(--surface-light); border: 1px solid var(--border); color: #fff; padding: 8px 15px; font-family: 'Orbitron'; font-size: 0.75rem; cursor: pointer; transition: 0.2s; }
                .sys-btn:hover { border-color: var(--accent); color: var(--accent); }

                .workspace-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 25px; }
                .panel-card { background: var(--surface); border: 1px solid var(--border); padding: 25px; display: flex; flex-direction: column; height: 480px; }
                .panel-title { font-family: 'Orbitron', monospace; font-size: 0.95rem; font-weight: 700; color: var(--accent); letter-spacing: 0.15em; margin-bottom: 15px; display: flex; align-items: center; gap: 10px; }

                .ai-chat-box { flex: 1; background: var(--bg); border: 1px solid var(--border); padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; margin-bottom: 12px; font-size: 0.95rem; }
                .ai-msg { padding: 10px 14px; border-radius: 2px; max-width: 85%; line-height: 1.5; }
                .ai-msg.system { background: var(--surface-light); border-left: 3px solid var(--accent); color: var(--primary); align-self: flex-start; }
                .ai-msg.user { background: rgba(255,0,127,0.15); border-right: 3px solid var(--accent); color: var(--primary); align-self: flex-end; }
                
                .ai-input-group { display: flex; gap: 10px; }
                .ai-input { flex: 1; background: var(--bg); border: 1px solid var(--border); padding: 10px; color: var(--primary); font-family: 'Rajdhani', sans-serif; font-size: 1rem; outline: none; }
                .ai-btn { background: var(--accent); color: #fff; border: none; padding: 0 18px; font-family: 'Orbitron', monospace; font-size: 0.75rem; font-weight: 700; cursor: pointer; }

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
                    <div class="admin-logo">INTERFORM<span>.INC</span> // ADMIN & SİSTEM ANALİZİ</div>
                    <div class="admin-nav">
                        <div class="badge">SİSTEM ANALİZİ AKTİF</div>
                        <a href="/store" class="logout-btn">MAĞAZA</a>
                        <a href="/" class="logout-btn">ÇIKIŞ</a>
                    </div>
                </div>

                <div class="stats-grid">
                    <div class="stat-box">
                        <div class="stat-title">SİSTEM DURUMU</div>
                        <div class="stat-value green">STABİL (%99.9)</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-title">AI OPERASYON MERKEZİ</div>
                        <div class="stat-value" style="color:var(--accent); font-size: 1.1rem; margin-top: 5px;">Qwen-3.8-27b</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-title">AKTİF OTURUMLAR</div>
                        <div class="stat-value">1,429</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-title">GÜVENLİK DUVARI</div>
                        <div class="stat-value green">AKTİF (TLS 1.3)</div>
                    </div>
                </div>

                <!-- SİSTEM ANALİZİ ÖZEL BÖLÜMÜ -->
                <div class="analysis-section">
                    <div class="panel-title" style="margin-bottom: 5px;">📊 CANLI SİSTEM ANALİZİ & PERFORMANS MONİTÖRÜ</div>
                    <p style="color:var(--secondary); font-size: 0.9rem;">Gerçek zamanlı mikroservis performans ve kaynak tüketim metrikleri.</p>
                    <div class="analysis-grid" id="analysisGrid">
                        <div class="analysis-card"><div class="analysis-label">CPU KULLANIMI</div><div class="analysis-val" id="cpuVal">Yükleniyor...</div></div>
                        <div class="analysis-card"><div class="analysis-label">RAM TÜKETİMİ</div><div class="analysis-val" id="ramVal" style="color:#3a86ff;">Yükleniyor...</div></div>
                        <div class="analysis-card"><div class="analysis-label">DİSK I/O</div><div class="analysis-val" id="diskVal" style="color:#00ff66;">Yükleniyor...</div></div>
                        <div class="analysis-card"><div class="analysis-label">AKTİF THREADLER</div><div class="analysis-val" id="threadVal">Yükleniyor...</div></div>
                    </div>
                    <div class="action-bar">
                        <button class="sys-btn" onclick="fetchSystemAnalysis()">🔄 METRİKLERİ YENİLE</button>
                        <button class="sys-btn" onclick="runAiSecurityAudit()">🛡️ AI GÜVENLİK ANALİZİ BAŞLAT</button>
                    </div>
                </div>

                <div class="workspace-grid">
                    <div class="panel-card">
                        <div class="panel-title">🤖 TAM YETKİLİ YAPAY ZEKA SİSTEM ANALİZİ</div>
                        <div class="ai-chat-box" id="chatBox">
                            <div class="ai-msg system">Sistem analizi hazır. Qwen-3.8-27b modeli tam yetkiyle çalışıyor. Güvenlik, altyapı veya performans hakkında rapor isteyebilirsiniz.</div>
                        </div>
                        <div class="ai-input-group">
                            <input type="text" id="aiPrompt" class="ai-input" placeholder="Sistem analizi veya komut iste..." onkeypress="checkEnter(event)">
                            <button class="ai-btn" onclick="sendAiQuery()">ÇALIŞTIR</button>
                        </div>
                    </div>

                    <div class="panel-card">
                        <div class="panel-title">🛡️ CANLI SİSTEM LOGLARI & DENETİM</div>
                        <div class="logs-container">
                            <div class="log-line">[11:00:01] [INFO] FastAPI sunucu başarıyla başlatıldı.</div>
                            <div class="log-line">[11:00:05] [AUTH] admin@interform.inc root yetkisiyle bağlandı.</div>
                            <div class="log-line">[11:00:12] [AI_CORE] Qwen-3.8-27b operasyonel asistan devrede.</div>
                            <div class="log-line">[11:00:20] [SECURITY] Güvenlik duvarı taraması tamamlandı (Tehdit yok).</div>
                            <div class="log-line" style="color:#ffaa00;">[11:01:00] [SYSTEM] Bellek analizi tamamlandı, optimize edildi.</div>
                        </div>
                    </div>
                </div>

                <div class="mgmt-grid">
                    <div class="mgmt-box">
                        <h3 style="font-family:'Orbitron'; color:var(--accent); font-size: 0.9rem;">📦 MAĞAZAYA ÜRÜN EKLE</h3>
                        <input type="text" id="pName" placeholder="Ürün Adı">
                        <input type="number" id="pPrice" placeholder="Fiyat ($)">
                        <input type="text" id="pCategory" placeholder="Kategori">
                        <input type="number" id="pStock" placeholder="Stok Adedi">
                        <button class="mgmt-btn" onclick="addProduct()">ÜRÜNÜ SİSTEME KAYDET</button>
                    </div>

                    <div class="mgmt-box">
                        <h3 style="font-family:'Orbitron'; color:#3a86ff; font-size: 0.9rem;">🛡️ E-POSTA İLE RÜTBE ATAMA</h3>
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
                            <option value="Administrator">Administrator (Admin Şifresi Gerekli)</option>
                        </select>
                        <input type="password" id="adminSecret" placeholder="Admin Şifresi (Sadece Administrator için)">
                        <button class="mgmt-btn" onclick="updateRank()">RÜTKEYİ GÜNCELLE</button>
                    </div>
                </div>
            </div>

            <script>
                async function fetchSystemAnalysis() {
                    try {
                        const res = await fetch('/api/admin/system-analysis');
                        const data = await res.json();
                        document.getElementById('cpuVal').innerText = data.cpu_usage;
                        document.getElementById('ramVal').innerText = data.ram_usage;
                        document.getElementById('diskVal').innerText = data.disk_io;
                        document.getElementById('threadVal').innerText = data.active_threads + " Aktif";
                    } catch (e) {
                        console.error("Analiz verisi alınamadı");
                    }
                }
                // Sayfa açıldığında ilk verileri yükle
                fetchSystemAnalysis();

                async function runAiSecurityAudit() {
                    const inputField = document.getElementById('aiPrompt');
                    inputField.value = "Kapsamlı bir sistem güvenlik ve performans analizi raporu oluştur.";
                    sendAiQuery();
                }

                async function sendAiQuery() {
                    const inputField = document.getElementById('aiPrompt');
                    const chatBox = document.getElementById('chatBox');
                    const prompt = inputField.value.trim();
                    if(!prompt) return;

                    chatBox.innerHTML += `<div class="ai-msg user">${escapeHtml(prompt)}</div>`;
                    inputField.value = '';
                    chatBox.scrollTop = chatBox.scrollHeight;

                    const loadingId = 'loading-' + Date.now();
                    chatBox.innerHTML += `<div class="ai-msg system" id="${loadingId}">Sistem analizi yapılıyor...</div>`;
                    chatBox.scrollTop = chatBox.scrollHeight;

                    try {
                        const res = await fetch('/api/ai-query', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ prompt })
                        });
                        const data = await res.json();
                        document.getElementById(loadingId).remove();
                        chatBox.innerHTML += `<div class="ai-msg system">${escapeHtml(data.response)}</div>`;
                    } catch (err) {
                        document.getElementById(loadingId).remove();
                        chatBox.innerHTML += `<div class="ai-msg system" style="color:#ff5555;">[HATA]: AI bağlantısı kurulamadı.</div>`;
                    }
                    chatBox.scrollTop = chatBox.scrollHeight;
                }

                function checkEnter(e) { if (e.key === 'Enter') { sendAiQuery(); } }
                function escapeHtml(text) { return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }

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
