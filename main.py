from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Statik dosyalar ve şablonlar (Varsa dizin yapına göre ayarlayabilirsin)
# app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    # templates/index.html dosyasını render eder
    return templates.TemplateResponse("index.html", {"request": request})

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

@app.get("/admin-dashboard", response_class=HTMLResponse)
async def admin_dashboard():
    return """
    <html>
        <head>
            <title>Interform Inc. | Admin Paneli</title>
            <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@400;600&display=swap" rel="stylesheet">
        </head>
        <body style="background:#070707; color:#fff; font-family:'Rajdhani',sans-serif; padding:50px;">
            <div style="max-width:800px; margin:0 auto; border:1px solid #262626; padding:40px; background:#111; box-shadow: 0 10px 30px rgba(0,0,0,0.8);">
                <h1 style="font-family:'Orbitron'; color:#3a86ff; margin-bottom:20px;">// ADMIN KONTROL PANELİ</h1>
                <p style="font-size: 1.1rem;">Hoş geldiniz, Yetkili Yönetici.</p>
                <div style="margin-top: 30px; padding: 20px; border: 1px solid #262626; background: #070707;">
                    <p style="margin-bottom: 10px; color:#999;">Sistem Durumu: <span style="color:#4caf7d;">Aktif & Çalışıyor</span></p>
                    <p style="color:#999;">AI Entegrasyonu: <span style="color:#3a86ff;">GroQ API Bağlı</span></p>
                </div>
                <a href="/" style="display:inline-block; margin-top:30px; padding:12px 24px; background:#fff; color:#000; text-decoration:none; font-family:'Orbitron'; font-size:0.8rem; font-weight:700; transition: opacity 0.2s;">ANA SAYFAYA DÖN</a>
            </div>
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
