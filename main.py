from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
import os
from groq import Groq

app = FastAPI()

# Örnek Kullanıcı ve Rol Veritabanı
USERS_DB = [
    {"id": 1, "email": "admin@interform.inc", "role": "Süper Admin", "status": "Aktif"},
    {"id": 2, "email": "berkay@interform.inc", "role": "Kurumsal Üye", "status": "Aktif"},
    {"id": 3, "email": "testuser@interform.inc", "role": "Standart Kullanıcı", "status": "Pasif"},
    {"id": 4, "email": "security@interform.inc", "role": "Güvenlik Sorumlusu", "status": "Aktif"}
]

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return """
    <html>
        <head>
            <title>Interform Inc. | Giriş</title>
            <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@400;600&display=swap" rel="stylesheet">
            <style>
                body { background: #070707; color: #fff; font-family: 'Rajdhani', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                .login-box { background: #111; border: 1px solid #262626; padding: 40px; width: 350px; display: flex; flex-direction: column; gap: 20px; }
                h1 { font-family: 'Orbitron', monospace; font-size: 1.2rem; letter-spacing: 0.1em; color: #3a86ff; margin: 0; }
                input { background: #070707; border: 1px solid #262626; padding: 12px; color: #fff; font-family: 'Rajdhani', sans-serif; font-size: 1rem; outline: none; }
                input:focus { border-color: #3a86ff; }
                button { background: #3a86ff; color: #fff; border: none; padding: 12px; font-family: 'Orbitron', monospace; font-weight: 700; cursor: pointer; }
                button:hover { opacity: 0.9; }
                .error { color: #ff5555; font-size: 0.85rem; display: none; }
            </style>
        </head>
        <body>
            <div class="login-box">
                <h1>// GİRİŞ YAP</h1>
                <div class="error" id="errorMsg">Geçersiz kimlik bilgileri.</div>
                <input type="email" id="email" placeholder="E-posta adresi">
                <input type="password" id="password" placeholder="Şifre">
                <button onclick="handleLogin()">BAĞLAN</button>
            </div>
            <script>
                async function handleLogin() {
                    const email = document.getElementById('email').value;
                    const password = document.getElementById('password').value;
                    const res = await fetch('/api/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ email, password })
                    });
                    const data = await res.json();
                    if(res.ok) {
                        window.location.href = data.redirect;
                    } else {
                        document.getElementById('errorMsg').style.display = 'block';
                    }
                }
            </script>
        </body>
    </html>
    """

@app.post("/api/login")
async def api_login(request: Request):
    data = await request.json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if email == "admin@interform.inc" and password == "admin123":
        return {"status": "success", "role": "admin", "redirect": "/admin-dashboard"}
    elif email and password:
        return {"status": "success", "role": "user", "redirect": "/dashboard"}
    
    raise HTTPException(status_code=400, detail="Geçersiz kimlik bilgileri.")

@app.post("/api/admin/ai-query")
async def admin_ai_query(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    api_key = os.environ.get("GROQ_API_KEY")
    
    if not api_key:
        return {"response": "[SİSTEM UYARISI]: GROQ_API_KEY çevre değişkeni bulunamadı! Simüle Edilen AI Yanıtı: Rol izin matrisi güncel ve kararlı."}
    
    try:
        client = Groq(api_key=api_key)
        chat_completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Sen Interform Inc. kurumsal yapay zeka asistanısın."},
                {"role": "user", "content": prompt}
            ]
        )
        return {"response": chat_completion.choices[0].message.content}
    except Exception as e:
        return {"response": f"AI Servis Hatası: {str(e)}"}

@app.post("/api/admin/update-role")
async def update_role(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    new_role = data.get("role")
    
    for user in USERS_DB:
        if user["id"] == user_id:
            user["role"] = new_role
            return {"status": "success", "message": f"Kullanıcı ID {user_id} rolü '{new_role}' olarak güncellendi."}
    
    raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

@app.get("/admin-dashboard", response_class=HTMLResponse)
async def admin_dashboard():
    users_html = ""
    for u in USERS_DB:
        sel_super = "selected" if u['role'] == "Süper Admin" else ""
        sel_corp = "selected" if u['role'] == "Kurumsal Üye" else ""
        sel_sec = "selected" if u['role'] == "Güvenlik Sorumlusu" else ""
        sel_std = "selected" if u['role'] == "Standart Kullanıcı" else ""
        status_color = "var(--success)" if u['status'] == "Aktif" else "#ffaa00"

        users_html += f"""
        <tr style="border-bottom: 1px solid var(--border);">
            <td style="padding: 12px; color: var(--secondary);">{u['id']}</td>
            <td style="padding: 12px; color: var(--primary); font-weight: 500;">{u['email']}</td>
            <td style="padding: 12px;">
                <select id="role-select-{u['id']}" style="background: var(--bg); color: var(--primary); border: 1px solid var(--border); padding: 6px 10px; font-family: 'Rajdhani', sans-serif;">
                    <option value="Süper Admin" {sel_super}>Süper Admin</option>
                    <option value="Kurumsal Üye" {sel_corp}>Kurumsal Üye</option>
                    <option value="Güvenlik Sorumlusu" {sel_sec}>Güvenlik Sorumlusu</option>
                    <option value="Standart Kullanıcı" {sel_std}>Standart Kullanıcı</option>
                </select>
            </td>
            <td style="padding: 12px;"><span style="color: {status_color};">{u['status']}</span></td>
            <td style="padding: 12px;">
                <button onclick="saveRole({u['id']})" style="background: var(--accent); color: #fff; border: none; padding: 6px 12px; font-family: 'Orbitron', monospace; font-size: 0.65rem; cursor: pointer; font-weight: 700;">GÜNCELLE</button>
            </td>
        </tr>
        """

    html_content = """
    <html>
        <head>
            <title>Interform Inc. | Kapsamlı Admin & Rol Yönetimi</title>
            <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=Rajdhani:wght@400;500;600;700&display=swap" rel="stylesheet">
            <style>
                :root {
                    --bg: #070707;
                    --surface: #111111;
                    --surface-light: #1a1a1a;
                    --border: #262626;
                    --primary: #ffffff;
                    --secondary: #999999;
                    --accent: #3a86ff;
                    --success: #4caf7d;
                }
                * { margin:0; padding:0; box-sizing:border-box; }
                body { background: var(--bg); color: var(--primary); font-family: 'Rajdhani', sans-serif; padding: 30px; min-height: 100vh; }
                .admin-container { max-width: 1400px; margin: 0 auto; display: flex; flex-direction: column; gap: 30px; }
                
                .admin-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 20px; }
                .admin-logo { font-family: 'Orbitron', monospace; font-size: 1.3rem; font-weight: 900; letter-spacing: 0.2em; color: var(--primary); }
                .admin-logo span { color: var(--accent); }
                .admin-nav { display: flex; gap: 15px; align-items: center; }
                .badge { background: rgba(58,134,255,0.1); border: 1px solid var(--accent); color: var(--accent); padding: 6px 14px; font-family: 'Orbitron', monospace; font-size: 0.7rem; letter-spacing: 0.1em; }
                .logout-btn { border: 1px solid var(--border); background: var(--surface); color: var(--secondary); padding: 8px 18px; font-family: 'Orbitron', monospace; font-size: 0.75rem; text-decoration: none; transition: 0.2s; }
                .logout-btn:hover { border-color: var(--primary); color: var(--primary); }

                .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
                .stat-box { background: var(--surface); border: 1px solid var(--border); padding: 25px; }
                .stat-title { font-family: 'Orbitron', monospace; font-size: 0.75rem; color: var(--secondary); letter-spacing: 0.15em; margin-bottom: 10px; }
                .stat-value { font-family: 'Orbitron', monospace; font-size: 1.8rem; font-weight: 700; color: var(--primary); }
                .stat-value.green { color: var(--success); }

                .workspace-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }
                .full-width-panel { background: var(--surface); border: 1px solid var(--border); padding: 30px; }
                .panel-card { background: var(--surface); border: 1px solid var(--border); padding: 30px; display: flex; flex-direction: column; height: 500px; }
                .panel-title { font-family: 'Orbitron', monospace; font-size: 1rem; font-weight: 700; color: var(--accent); letter-spacing: 0.15em; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }
                
                .ai-chat-box { flex: 1; background: var(--bg); border: 1px solid var(--border); padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 15px; margin-bottom: 15px; font-size: 0.95rem; }
                .ai-msg { padding: 10px 14px; border-radius: 2px; max-width: 85%; line-height: 1.5; }
                .ai-msg.system { background: var(--surface-light); border-left: 3px solid var(--accent); color: var(--primary); align-self: flex-start; }
                .ai-msg.user { background: rgba(58,134,255,0.15); border-right: 3px solid var(--accent); color: var(--primary); align-self: flex-end; }
                
                .ai-input-group { display: flex; gap: 10px; }
                .ai-input { flex: 1; background: var(--bg); border: 1px solid var(--border); padding: 12px; color: var(--primary); font-family: 'Rajdhani', sans-serif; font-size: 1rem; outline: none; }
                .ai-input:focus { border-color: var(--accent); }
                .ai-btn { background: var(--accent); color: #fff; border: none; padding: 0 20px; font-family: 'Orbitron', monospace; font-size: 0.75rem; font-weight: 700; cursor: pointer; letter-spacing: 0.1em; }
                .ai-btn:hover { opacity: 0.9; }

                #toast { position: fixed; bottom: 20px; right: 20px; background: var(--success); color: #000; padding: 12px 24px; font-family: 'Orbitron', monospace; font-size: 0.8rem; font-weight: 700; display: none; z-index: 9999; }

                @media(max-width: 1024px) {
                    .stats-grid { grid-template-columns: repeat(2, 1fr); }
                    .workspace-grid { grid-template-columns: 1fr; }
                }
            </style>
        </head>
        <body>
            <div id="toast">Rol başarıyla güncellendi!</div>
            <div class="admin-container">
                <div class="admin-header">
                    <div class="admin-logo">INTERFORM<span>.INC</span> // YÖNETİM & YETKİ MERKEZİ</div>
                    <div class="admin-nav">
                        <div class="badge">SÜPER ADMIN OTURUMU</div>
                        <a href="/" class="logout-btn">ÇIKIŞ YAP</a>
                    </div>
                </div>

                <div class="stats-grid">
                    <div class="stat-box">
                        <div class="stat-title">SİSTEM DURUMU</div>
                        <div class="stat-value green">STABİL</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-title">YAPAY ZEKA MODELİ</div>
                        <div class="stat-value" style="font-size: 1.2rem; margin-top: 5px; color: var(--accent);">Llama-3.3-70b</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-title">TOPLAM KULLANICI</div>
                        <div class="stat-value">4</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-title">GÜVENLİK DUVARI</div>
                        <div class="stat-value green">AKTİF</div>
                    </div>
                </div>

                <div class="full-width-panel">
                    <div class="panel-title">👥 KULLANICI & ROL YETKİLENDİRME MATRİSİ</div>
                    <div style="overflow-x: auto;">
                        <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.95rem;">
                            <thead>
                                <tr style="border-bottom: 2px solid var(--border); font-family: 'Orbitron', monospace; font-size: 0.75rem; color: var(--secondary);">
                                    <th style="padding: 12px;">ID</th>
                                    <th style="padding: 12px;">E-POSTA</th>
                                    <th style="padding: 12px;">ATANAN ROL</th>
                                    <th style="padding: 12px;">DURUM</th>
                                    <th style="padding: 12px;">İŞLEM</th>
                                </tr>
                            </thead>
                            <tbody>
                                __USERS_HTML_PLACEHOLDER__
                            </tbody>
                        </table>
                    </div>
                </div>

                <div class="workspace-grid">
                    <div class="panel-card">
                        <div class="panel-title">🤖 GROQ AI YETKİ & GÜVENLİK ASİSTANI</div>
                        <div class="ai-chat-box" id="chatBox">
                            <div class="ai-msg system">Yönetici paneline hoş geldiniz. Rol matrisi ve yetkilendirmeler hakkında AI'ya danışabilirsiniz.</div>
                        </div>
                        <div class="ai-input-group">
                            <input type="text" id="aiPrompt" class="ai-input" placeholder="AI'ya komut ver..." onkeypress="checkEnter(event)">
                            <button class="ai-btn" onclick="sendAiQuery()">GÖNDER</button>
                        </div>
                    </div>

                    <div class="panel-card">
                        <div class="panel-title">🛡️ CANLI ERİŞİM VE GÜVENLİK LOGLARI</div>
                        <div style="flex: 1; background: var(--bg); border: 1px solid var(--border); padding: 15px; overflow-y: auto; font-family: 'Courier New', monospace; font-size: 0.85rem; color: #00ff66; display: flex; flex-direction: column; gap: 8px;">
                            <div style="border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 4px;">[10:38:40] [INFO] FastAPI sunucu başarıyla başlatıldı.</div>
                            <div style="border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 4px;">[10:38:42] [AUTH] admin@interform.inc oturum açtı.</div>
                            <div style="border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 4px;">[10:39:00] [RBAC] Rol matrisi doğrulandı.</div>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                async function saveRole(userId) {
                    const selectElement = document.getElementById('role-select-' + userId);
                    const newRole = selectElement.value;

                    try {
                        const res = await fetch('/api/admin/update-role', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ user_id: userId, role: newRole })
                        });
                        const data = await res.json();
                        if(res.ok) {
                            showToast(data.message);
                        } else {
                            alert('Hata oluştu!');
                        }
                    } catch(err) {
                        alert('Sunucu bağlantı hatası!');
                    }
                }

                function showToast(msg) {
                    const toast = document.getElementById('toast');
                    toast.innerText = msg;
                    toast.style.display = 'block';
                    setTimeout(() => { toast.style.display = 'none'; }, 3000);
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
                    chatBox.innerHTML += `<div class="ai-msg system" id="${loadingId}">AI analiz yapıyor...</div>`;
                    chatBox.scrollTop = chatBox.scrollHeight;

                    try {
                        const res = await fetch('/api/admin/ai-query', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ prompt })
                        });
                        const data = await res.json();
                        document.getElementById(loadingId).remove();
                        chatBox.innerHTML += `<div class="ai-msg system">${escapeHtml(data.response)}</div>`;
                    } catch (err) {
                        document.getElementById(loadingId).remove();
                        chatBox.innerHTML += `<div class="ai-msg system" style="color:#ff5555;">[HATA]: AI yanıt veremedi.</div>`;
                    }
                    chatBox.scrollTop = chatBox.scrollHeight;
                }

                function checkEnter(e) {
                    if (e.key === 'Enter') { sendAiQuery(); }
                }

                function escapeHtml(text) {
                    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
                }
            </script>
        </body>
    </html>
    """
    
    return html_content.replace("__USERS_HTML_PLACEHOLDER__", users_html)

@app.get("/dashboard", response_class=HTMLResponse)
async def user_dashboard():
    return """
    <html>
        <head><title>Interform Inc. | Kullanıcı Paneli</title>
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@400;600&display=swap" rel="stylesheet">
        </head>
        <body style="background:#070707; color:#fff; font-family:'Rajdhani',sans-serif; padding:50px;">
            <div style="max-width:800px; margin:0 auto; border:1px solid #262626; padding:40px; background:#111;">
                <h1 style="font-family:'Orbitron'; color:#fff; margin-bottom:20px;">// KULLANICI PORTALI</h1>
                <p>Kullanıcı paneline hoş geldiniz.</p>
                <a href="/" style="display:inline-block; margin-top:30px; padding:10px 20px; background:#fff; color:#000; text-decoration:none; font-family:'Orbitron'; font-size:0.8rem; font-weight:700;">ANA SAYFAYA DÖN</a>
            </div>
        </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
