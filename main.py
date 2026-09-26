from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from groq import Groq

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# --- SİSTEM VE ENJEKTÖR VERİTABANI SİMÜLASYONU ---
SYSTEM_STATE = {
    "status": "STABİL",
    "cpu": "18.4%",
    "ram": "4.2 GB / 16 GB",
    "active_threats": 0,
    "memory_leak_simulated": False
}

# Gündemdeki Popüler Oyunlar Enjektör Listesi
INJECTORS = [
    {"id": "cs2", "name": "Counter-Strike 2", "engine": "Source 2", "status": "UNDETECTED", "version": "v4.2.1", "downloads": 1420},
    {"id": "valorant", "name": "Valorant (Vanguard Bypass)", "engine": "Unreal Engine 4/5", "status": "UNDETECTED", "version": "v2.8.4", "downloads": 3100},
    {"id": "gta5", "name": "GTA V / FiveM", "engine": "RAGE Engine", "status": "UNDETECTED", "version": "v5.0.0", "downloads": 2450},
    {"id": "apex", "name": "Apex Legends", "engine": "Source", "status": "UPDATING", "version": "v1.9.2", "downloads": 980},
    {"id": "fortnite", "name": "Fortnite", "engine": "Unreal Engine 5", "status": "UNDETECTED", "version": "v3.1.0", "downloads": 1890}
]

# Kullanıcılardan gelen özel istek enjektörleri
CUSTOM_REQUESTS = [
    {"id": 1, "game": "Project Zomboid", "user": "agent_47@interform.inc", "status": "İşleme Alındı", "priority": "Orta"}
]

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

# --- ENJEKTÖR YÖNETİM ENDPOINTLERİ ---
@app.get("/api/injectors")
async def get_injectors():
    return {"injectors": INJECTORS, "requests": CUSTOM_REQUESTS}

@app.post("/api/admin/add-injector")
async def add_injector(request: Request):
    data = await request.json()
    new_id = data.get("id", "custom_game")
    INJECTORS.append({
        "id": new_id,
        "name": data.get("name"),
        "engine": data.get("engine", "Custom"),
        "status": "UNDETECTED",
        "version": data.get("version", "v1.0.0"),
        "downloads": 0
    })
    return {"status": "success", "message": f"{data.get('name')} için enjektör modülü sisteme eklendi."}

@app.post("/api/user/request-injector")
async def request_injector(request: Request):
    data = await request.json()
    game_name = data.get("game", "").strip()
    email = data.get("email", "misafir@interform.inc")
    
    if not game_name:
        raise HTTPException(status_code=400, detail="Oyun adı boş olamaz.")
        
    CUSTOM_REQUESTS.append({
        "id": len(CUSTOM_REQUESTS) + 1,
        "game": game_name,
        "user": email,
        "status": "İnceleniyor (Sırada)",
        "priority": "Özel İstek"
    })
    return {"status": "success", "message": f"'{game_name}' için özel enjektör talebiniz sıraya alındı."}

# --- SİSTEM ANALİZİ VE OTONOM TETİKLEYİCİ API ---
@app.get("/api/admin/system-analysis")
async def get_system_analysis():
    return {
        "cpu_usage": SYSTEM_STATE["cpu"],
        "ram_usage": SYSTEM_STATE["ram"],
        "disk_io": "1.2 MB/s",
        "active_threads": 48,
        "network_traffic": "450 KB/s",
        "database_status": SYSTEM_STATE["status"],
        "security_threats": SYSTEM_STATE["active_threats"],
        "ai_status": "Active (Qwen-3.8-27b Self-Healing Enabled)"
    }

@app.post("/api/admin/inject-fault")
async def inject_fault():
    SYSTEM_STATE["status"] = "KRİTİK UYARI (Bellek Sızıntısı)"
    SYSTEM_STATE["cpu"] = "%94.2 (Aşırı Yük)"
    SYSTEM_STATE["ram"] = "15.1 GB / 16 GB"
    SYSTEM_STATE["active_threats"] = 2
    SYSTEM_STATE["memory_leak_simulated"] = True
    return {"status": "success", "message": "Sisteme simüle edilmiş bellek sızıntısı ve performans darboğazı enjekte edildi."}

# --- TAM YETKİLİ VE OTONOM AI ENDPOINTİ ---
@app.post("/api/ai-query")
async def ai_query(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "").lower()
    
    action_taken = ""
    if "onar" in prompt or "fix" in prompt or "çöz" in prompt or "optimize" in prompt or "temizle" in prompt:
        if SYSTEM_STATE["memory_leak_simulated"] or SYSTEM_STATE["active_threats"] > 0 or "KRİTİK" in SYSTEM_STATE["status"]:
            SYSTEM_STATE["status"] = "STABİL"
            SYSTEM_STATE["cpu"] = "19.1%"
            SYSTEM_STATE["ram"] = "4.4 GB / 16 GB"
            SYSTEM_STATE["active_threats"] = 0
            SYSTEM_STATE["memory_leak_simulated"] = False
            action_taken = "\n\n[OTONOM İŞLEM BAŞARILI]: AI çekirdeği bellek sızıntısını izole etti, önbelleği temizledi ve sistem kararlılığını geri getirdi."
        else:
            action_taken = "\n\n[OTONOM BİLGİ]: Sistem halihazırda tamamen stabil çalışıyor."

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {"response": f"[SİSTEM UYARISI]: GROQ_API_KEY bulunamadı! Simüle Edilen Otonom Yanıt: İşlem tamamlandı.{action_taken}"}
    
    try:
        client = Groq(api_key=api_key)
        system_context = f"""
        Sen Interform Inc.'in tam yetkili, otonom başmühendis ve hile/enjektör operasyonları sorumlusu yapay zeka asistanısın (Model: Qwen-3.8-27b).
        Şu anki Anlık Sistem Durumu:
        - Durum: {SYSTEM_STATE['status']}
        - CPU: {SYSTEM_STATE['cpu']}
        - RAM: {SYSTEM_STATE['ram']}
        """
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_context},
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
            <title>Interform Inc. | Mağaza & Enjektör Portali</title>
            <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@400;600&display=swap" rel="stylesheet">
            <style>
                body { background: #070707; color: #fff; font-family: 'Rajdhani', sans-serif; padding: 40px; }
                .container { max-width: 1100px; margin: 0 auto; }
                .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 30px; }
                .card { background: #111; border: 1px solid #262626; padding: 20px; }
                .btn { background: #ff007f; color: #fff; border: none; padding: 10px 15px; font-family: 'Orbitron'; cursor: pointer; margin-top: 10px; width: 100%; }
                .request-box { background: #111; border: 1px solid #262626; padding: 25px; margin-top: 40px; }
                input { width: 100%; padding: 10px; background: #070707; border: 1px solid #262626; color: #fff; margin-top: 10px; font-family: inherit; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1 style="font-family:'Orbitron'; color:#ff007f;">// OYUN ENJEKTÖRLERİ & MAĞAZA</h1>
                <a href="/admin-dashboard" style="color:#aaa; text-decoration:none;">&larr; Yönetim Paneli</a>
                
                <h2 style="font-family:'Orbitron'; margin-top:30px; font-size:1.1rem; color:#4caf7d;">Aktif Oyun Modülleri</h2>
                <div class="grid" id="injectorGrid"></div>

                <div class="request-box">
                    <h3 style="font-family:'Orbitron'; color:#3a86ff; font-size:1rem;">🎯 ÖZEL OYUN / ENJEKTÖR İSTEĞİ</h3>
                    <p style="color:#aaa; font-size:0.9rem; margin-top:5px;">Listede olmayan küçük çaplı veya indie bir oyun için enjektör talebinde bulunun.</p>
                    <input type="text" id="reqGame" placeholder="İstediğiniz Oyunun Adı (örn: Lethal Company)">
                    <button class="btn" style="background:#3a86ff;" onclick="submitRequest()">ÖZEL TALEP OLUŞTUR</button>
                </div>
            </div>
            <script>
                fetch('/api/injectors').then(res => res.json()).then(data => {
                    const grid = document.getElementById('injectorGrid');
                    data.injectors.forEach(inj => {
                        grid.innerHTML += `
                            <div class="card">
                                <h3 style="font-family:'Orbitron';">${inj.name}</h3>
                                <p style="color:#aaa;">Motor: ${inj.engine}</p>
                                <p style="color:#aaa;">Sürüm: ${inj.version}</p>
                                <p style="color:#4caf7d; font-weight:bold; margin-top:10px;">DURUM: ${inj.status}</p>
                                <button class="btn" onclick="alert('${inj.name} enjektör paketi indiriliyor...')">İNDİR / ENJEKTE ET</button>
                            </div>
                        `;
                    });
                });

                async function submitRequest() {
                    const game = document.getElementById('reqGame').value;
                    const res = await fetch('/api/user/request-injector', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({game})
                    });
                    const data = await res.json();
                    alert(data.message);
                    document.getElementById('reqGame').value = '';
                }
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
                button { width: 22%; background: #ff007f; color: #fff; border: none; cursor: pointer; font-family: 'Orbitron'; }
            </style>
        </head>
        <body>
            <div class="box">
                <h1 style="font-family:'Orbitron'; color:#ff007f;">// KULLANICI & AI PORTALI</h1>
                <p>Hoş geldiniz. Enjektörler için mağazayı ziyaret edebilir veya AI asistanından destek alabilirsiniz.</p>
                <a href="/store" style="color:#ff007f;">Enjektör Mağazasına Git</a> | <a href="/" style="color:#aaa;">Çıkış Yap</a>
                
                <h3 style="font-family:'Orbitron'; margin-top:20px;">🤖 Qwen AI Asistanı</h3>
                <div class="chat" id="chatBox"><div style="color:#888;">AI Başmühendis hazır. Sorunuzu yazın...</div></div>
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
                    box.innerHTML += `<div style="color:#ff007f; margin-top:5px;"><b>AI:</b> ${data.response}</div>`;
                    box.scrollTop = box.scrollHeight;
                }
            </script>
        </body>
    </html>
    """

# --- GELİŞMİŞ YÖNETİCİ PANELİ ---
@app.get("/admin-dashboard", response_class=HTMLResponse)
async def admin_dashboard():
    return """
    <html>
        <head>
            <title>Interform | Otonom Yönetici Paneli</title>
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
                .stat-value { font-family: 'Orbitron', monospace; font-size: 1.4rem; font-weight: 700; color: var(--primary); }
                .stat-value.green { color: var(--success); }
                .stat-value.warning { color: var(--warning); }

                .analysis-section { background: var(--surface); border: 1px solid var(--border); padding: 25px; }
                .analysis-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top: 15px; }
                .analysis-card { background: var(--bg); border: 1px solid var(--border); padding: 15px; }
                .analysis-label { font-size: 0.8rem; color: var(--secondary); font-family: 'Orbitron', monospace; }
                .analysis-val { font-size: 1.2rem; font-weight: 700; color: var(--warning); margin-top: 5px; font-family: 'Orbitron', monospace; }
                .action-bar { margin-top: 15px; display: flex; gap: 10px; flex-wrap: wrap; }
                .sys-btn { background: var(--surface-light); border: 1px solid var(--border); color: #fff; padding: 8px 15px; font-family: 'Orbitron'; font-size: 0.75rem; cursor: pointer; transition: 0.2s; }
                .sys-btn:hover { border-color: var(--accent); color: var(--accent); }
                .sys-btn.danger { border-color: rgba(255,0,127,0.4); color: var(--accent); }

                .workspace-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 25px; }
                .panel-card { background: var(--surface); border: 1px solid var(--border); padding: 25px; display: flex; flex-direction: column; height: 480px; }
                .panel-title { font-family: 'Orbitron', monospace; font-size: 0.95rem; font-weight: 700; color: var(--accent); letter-spacing: 0.15em; margin-bottom: 15px; display: flex; align-items: center; gap: 10px; }

                .ai-chat-box { flex: 1; background: var(--bg); border: 1px solid var(--border); padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; margin-bottom: 12px; font-size: 0.95rem; }
                .ai-msg { padding: 10px 14px; border-radius: 2px; max-width: 85%; line-height: 1.5; white-space: pre-wrap; }
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
                    <div class="admin-logo">INTERFORM<span>.INC</span> // ENJEKTÖR & SİSTEM YÖNETİMİ</div>
                    <div class="admin-nav">
                        <div class="badge">SELF-HEALING AI AKTİF</div>
                        <a href="/store" class="logout-btn">ENJEKTÖR MAĞAZASI</a>
                        <a href="/" class="logout-btn">ÇIKIŞ</a>
                    </div>
                </div>

                <div class="stats-grid">
                    <div class="stat-box">
                        <div class="stat-title">SİSTEM DURUMU</div>
                        <div class="stat-value green" id="statStatus">STABİL</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-title">AI BAŞMÜHENDİS</div>
                        <div class="stat-value" style="color:var(--accent); font-size: 1.1rem; margin-top: 5px;">Qwen-3.8-27b</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-title">AKTİF OTURUMLAR</div>
                        <div class="stat-value">1,429</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-title">GÜVENLİK DUVARI</div>
                        <div class="stat-value green" id="statThreats">AKTİF (0 Tehdit)</div>
                    </div>
                </div>

                <!-- SİSTEM ANALİZİ & TEST BÖLÜMÜ -->
                <div class="analysis-section">
                    <div class="panel-title" style="margin-bottom: 5px;">📊 CANLI SİSTEM ANALİZİ & OTONOM ONARIM KONTROLÜ</div>
                    <p style="color:var(--secondary); font-size: 0.9rem;">Yapay zeka asistanı sistem metriklerini izler. Test için hata enjekte edebilir, ardından AI'ya onartabilirsiniz.</p>
                    <div class="analysis-grid" id="analysisGrid">
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
                        <div class="panel-title">🤖 TAM YETKİLİ YAPAY ZEKA SİSTEM ANALİZİ</div>
                        <div class="ai-chat-box" id="chatBox">
                            <div class="ai-msg system">Otonom AI Başmühendis hazır. "Sistemi tara ve onar" komutuyla arka plandaki tüm anormallikleri özerk bir şekilde giderebilirim.</div>
                        </div>
                        <div class="ai-input-group">
                            <input type="text" id="aiPrompt" class="ai-input" placeholder="Sistem analizi veya onarım iste..." onkeypress="checkEnter(event)">
                            <button class="ai-btn" onclick="sendAiQuery()">ÇALIŞTIR</button>
                        </div>
                    </div>

                    <div class="panel-card">
                        <div class="panel-title">🛡️ CANLI SİSTEM LOGLARI & DENETİM</div>
                        <div class="logs-container" id="logsContainer">
                            <div class="log-line">[22:00:01] [INFO] FastAPI sunucu başarıyla başlatıldı.</div>
                            <div class="log-line">[22:00:05] [AUTH] admin@interform.inc root yetkisiyle bağlandı.</div>
                            <div class="log-line">[22:00:12] [INJECTOR_CORE] Popüler oyun modülleri yüklendi.</div>
                            <div class="log-line">[22:00:20] [SECURITY] Vanguard ve BattlEye bypass simülasyonu aktif.</div>
                        </div>
                    </div>
                </div>

                <div class="mgmt-grid">
                    <div class="mgmt-box">
                        <h3 style="font-family:'Orbitron'; color:var(--accent); font-size: 0.9rem;">🎯 YENİ ENJEKTÖR MODÜLÜ EKLE</h3>
                        <input type="text" id="injId" placeholder="ID (örn: pubg)">
                        <input type="text" id="injName" placeholder="Oyun Adı">
                        <input type="text" id="injEngine" placeholder="Oyun Motoru (Unreal vb.)">
                        <input type="text" id="injVersion" placeholder="Sürüm (v1.0.0)">
                        <button class="mgmt-btn" onclick="addInjectorModule()">ENJEKTÖRÜ SİSTEME EKLE</button>
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
                        
                        const statStatus = document.getElementById('statStatus');
                        statStatus.innerText = data.database_status;
                        if(data.database_status.includes("KRİTİK")) {
                            statStatus.className = "stat-value warning";
                        } else {
                            statStatus.className = "stat-value green";
                        }

                        const statThreats = document.getElementById('statThreats');
                        if(data.security_threats > 0) {
                            statThreats.innerText = `ALARM (${data.security_threats} Tehdit)`;
                            statThreats.className = "stat-value warning";
                        } else {
                            statThreats.innerText = "AKTİF (0 Tehdit)";
                            statThreats.className = "stat-value green";
                        }
                    } catch (e) {
                        console.error("Analiz verisi alınamadı");
                    }
                }
                fetchSystemAnalysis();
                setInterval(fetchSystemAnalysis, 5000);

                async function injectFault() {
                    const res = await fetch('/api/admin/inject-fault', { method: 'POST' });
                    const data = await res.json();
                    alert(data.message);
                    
                    const logs = document.getElementById('logsContainer');
                    logs.innerHTML += `<div class="log-line" style="color:#ffaa00;">[WARNING] Simüle edilmiş bellek sızıntısı ve performans düşüşü algılandı!</div>`;
                    logs.scrollTop = logs.scrollHeight;
                    fetchSystemAnalysis();
                }

                function askAiToHeal() {
                    const inputField = document.getElementById('aiPrompt');
                    inputField.value = "Sistemi tara, tespit edilen tüm bellek sızıntılarını ve açıkları kendi kendine onar.";
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
                    chatBox.innerHTML += `<div class="ai-msg system" id="${loadingId}">Otonom analiz ve müdahale gerçekleştiriliyor...</div>`;
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
                        
                        const logs = document.getElementById('logsContainer');
                        logs.innerHTML += `<div class="log-line" style="color:#00ff66;">[AI_HEAL] Otonom onarım ve optimizasyon döngüsü uygulandı.</div>`;
                        logs.scrollTop = logs.scrollHeight;

                        fetchSystemAnalysis();
                    } catch (err) {
                        document.getElementById(loadingId).remove();
                        chatBox.innerHTML += `<div class="ai-msg system" style="color:#ff5555;">[HATA]: AI bağlantısı kurulamadı.</div>`;
                    }
                    chatBox.scrollTop = chatBox.scrollHeight;
                }

                function checkEnter(e) { if (e.key === 'Enter') { sendAiQuery(); } }
                function escapeHtml(text) { return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }

                async function addInjectorModule() {
                    const id = document.getElementById('injId').value;
                    const name = document.getElementById('injName').value;
                    const engine = document.getElementById('injEngine').value;
                    const version = document.getElementById('injVersion').value;
                    
                    const res = await fetch('/api/admin/add-injector', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({id, name, engine, version})
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
