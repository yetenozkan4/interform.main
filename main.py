from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
# Groq kütüphanesini kullanıyorsan import edebilirsin, alternatif olarak request simülasyonu da yapabiliriz.
# pip install groq
from groq import Groq

app = FastAPI()

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})

@app.post("/api/login")
async def api_login(request: Request):
    data = await request.json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # Admin kontrolü
    if email == "admin@interform.inc" and password == "admin123":
        return {"status": "success", "role": "admin", "redirect": "/admin-dashboard"}
    elif email and password:
        return {"status": "success", "role": "user", "redirect": "/dashboard"}
    
    raise HTTPException(status_code=400, detail="Geçersiz kimlik bilgileri.")

# YAPAY ZEKA API ENDPOINT (Admin Paneli İçinden Çağrılır)
@app.post("/api/admin/ai-query")
async def admin_ai_query(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    
    api_key = os.environ.get("GROQ_API_KEY")
    
    if not api_key:
        return {"response": "[SİSTEM UYARISI]: GROQ_API_KEY çevre değişkeni bulunamadı! Simüle Edilen AI Yanıtı: Sistem durumu normal, güvenlik duvarları aktif ve tüm mikroservisler stabil çalışıyor."}
    
    try:
        client = Groq(api_key=api_key)
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Sen Interform Inc. kurumsal yapay zeka asistanısın. Admin paneli için sistem analizi, güvenlik raporları ve teknik destek sağlıyorsun. Profesyonel, siberpunk ve teknik bir üslubun var."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
        }
        answer = chat_completion.choices[0].message.content
        return {"response": answer}
    except Exception as e:
        return {"response": f"AI Servis Hatası: {str(e)}"}

@app.get("/admin-dashboard", response_class=HTMLResponse)
async def admin_dashboard():
    return """
    <html>
        <head>
            <title>Interform Inc. | Gelişmiş Admin & AI Paneli</title>
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
                .admin-container { max-width: 1300px; margin: 0 auto; display: flex; flex-direction: column; gap: 30px; }
                
                /* Header */
                .admin-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 20px; }
                .admin-logo { font-family: 'Orbitron', monospace; font-size: 1.3rem; font-weight: 900; letter-spacing: 0.2em; color: var(--primary); }
                .admin-logo span { color: var(--accent); }
                .admin-nav { display: flex; gap: 15px; align-items: center; }
                .badge { background: rgba(58,134,255,0.1); border: 1px solid var(--accent); color: var(--accent); padding: 6px 14px; font-family: 'Orbitron', monospace; font-size: 0.7rem; letter-spacing: 0.1em; }
                .logout-btn { border: 1px solid var(--border); background: var(--surface); color: var(--secondary); padding: 8px 18px; font-family: 'Orbitron', monospace; font-size: 0.75rem; text-decoration: none; transition: 0.2s; }
                .logout-btn:hover { border-color: var(--primary); color: var(--primary); }

                /* Stats Grid */
                .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
                .stat-box { background: var(--surface); border: 1px solid var(--border); padding: 25px; }
                .stat-title { font-family: 'Orbitron', monospace; font-size: 0.75rem; color: var(--secondary); letter-spacing: 0.15em; margin-bottom: 10px; }
                .stat-value { font-family: 'Orbitron', monospace; font-size: 1.8rem; font-weight: 700; color: var(--primary); }
                .stat-value.green { color: var(--success); }

                /* Main Workspace Grid */
                .workspace-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }
                .panel-card { background: var(--surface); border: 1px solid var(--border); padding: 30px; display: flex; flex-direction: column; height: 500px; }
                .panel-title { font-family: 'Orbitron', monospace; font-size: 1rem; font-weight: 700; color: var(--accent); letter-spacing: 0.15em; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }
                
                /* AI Chat Box */
                .ai-chat-box { flex: 1; background: var(--bg); border: 1px solid var(--border); padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 15px; margin-bottom: 15px; font-size: 0.95rem; }
                .ai-msg { padding: 10px 14px; border-radius: 2px; max-width: 85%; line-height: 1.5; }
                .ai-msg.system { background: var(--surface-light); border-left: 3px solid var(--accent); color: var(--primary); align-self: flex-start; }
                .ai-msg.user { background: rgba(58,134,255,0.15); border-right: 3px solid var(--accent); color: var(--primary); align-self: flex-end; }
                
                .ai-input-group { display: flex; gap: 10px; }
                .ai-input { flex: 1; background: var(--bg); border: 1px solid var(--border); padding: 12px; color: var(--primary); font-family: 'Rajdhani', sans-serif; font-size: 1rem; outline: none; }
                .ai-input:focus { border-color: var(--accent); }
                .ai-btn { background: var(--accent); color: #fff; border: none; padding: 0 20px; font-family: 'Orbitron', monospace; font-size: 0.75rem; font-weight: 700; cursor: pointer; letter-spacing: 0.1em; }
                .ai-btn:hover { opacity: 0.9; }

                /* Logs / Quick Actions */
                .logs-container { flex: 1; background: var(--bg); border: 1px solid var(--border); padding: 15px; overflow-y: auto; font-family: 'Courier New', monospace; font-size: 0.85rem; color: #00ff66; display: flex; flex-direction: column; gap: 8px; }
                .log-line { border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 4px; }
                
                @media(max-width: 1024px) {
                    .stats-grid { grid-template-columns: repeat(2, 1fr); }
                    .workspace-grid { grid-template-columns: 1fr; }
                }
            </style>
        </head>
        <body>
            <div class="admin-container">
                <!-- Header -->
                <div class="admin-header">
                    <div class="admin-logo">INTERFORM<span>.INC</span> // ADMIN KONTROL</div>
                    <div class="admin-nav">
                        <div class="badge">GROQ AI AKTİF</div>
                        <a href="/" class="logout-btn">GÜVENLİ ÇIKIŞ</a>
                    </div>
                </div>

                <!-- Stats -->
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
                        <div class="stat-title">AKTİF OTURUMLAR</div>
                        <div class="stat-value">1,429</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-title">GÜVENLİK DUVARI</div>
                        <div class="stat-value green">AKTİF</div>
                    </div>
                </div>

                <!-- Workspace (AI & Logs) -->
                <div class="workspace-grid">
                    <!-- AI Panel -->
                    <div class="panel-card">
                        <div class="panel-title">🤖 GROQ AI OPERASYONEL ASİSTANI</div>
                        <div class="ai-chat-box" id="chatBox">
                            <div class="ai-msg system">Sistem yöneticisi bağlandı. GroQ LLM entegrasyonu hazır. Sunucu analizi, kod optimizasyonu veya güvenlik taraması için komut verebilirsiniz.</div>
                        </div>
                        <div class="ai-input-group">
                            <input type="text" id="aiPrompt" class="ai-input" placeholder="AI'ya komut ver (Örn: Sunucu sağlığını analiz et...)" onkeypress="checkEnter(event)">
                            <button class="ai-btn" onclick="sendAiQuery()">GÖNDER</button>
                        </div>
                    </div>

                    <!-- System Logs -->
                    <div class="panel-card">
                        <div class="panel-title">🛡️ CANLI SİSTEM LOGLARI & DENETİM</div>
                        <div class="logs-container">
                            <div class="log-line">[10:38:40] [INFO] FastAPI sunucu başarıyla başlatıldı.</div>
                            <div class="log-line">[10:38:42] [AUTH] admin@interform.inc başarıyla oturum açtı.</div>
                            <div class="log-line">[10:38:45] [AI_ENGINE] Groq istemci bağlantısı test edildi (OK).</div>
                            <div class="log-line">[10:39:02] [SECURITY] Uçtan uca TLS 1.3 şifreleme aktif.</div>
                            <div class="log-line" style="color: #ffaa00;">[10:39:15] [WARN] Yüksek trafik algılandı (US-East Cluster).</div>
                            <div class="log-line">[10:40:00] [SYSTEM] Bellek kullanımı optimize edildi (%24).</div>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                async function sendAiQuery() {
                    const inputField = document.getElementById('aiPrompt');
                    const chatBox = document.getElementById('chatBox');
                    const prompt = inputField.value.trim();
                    if(!prompt) return;

                    // Kullanıcı mesajını ekle
                    chatBox.innerHTML += `<div class="ai-msg user">${escapeHtml(prompt)}</div>`;
                    inputField.value = '';
                    chatBox.scrollTop = chatBox.scrollHeight;

                    // Yükleniyor mesajı
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
                        chatBox.innerHTML += `<div class="ai-msg system" style="color:#ff5555;">[HATA]: AI sunucusuna bağlanılamadı.</div>`;
                    }
                    chatBox.scrollTop = chatBox.scrollHeight;
                }

                function checkEnter(e) {
                    if (e.key === 'Enter') {
                        sendAiQuery();
                    }
                }

                function escapeHtml(text) {
                    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
                }
            </script>
        </body>
    </html>
    """

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
