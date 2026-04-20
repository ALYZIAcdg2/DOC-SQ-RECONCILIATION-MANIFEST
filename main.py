import os
import base64
import httpx
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

app = FastAPI()

# --- FONCTION D'ENVOI VIA SENDGRID ---
async def envoyer_email_sendgrid(pdf_content, filename, subject, body):
    API_KEY = os.environ.get("SENDGRID_API_KEY")
    if not API_KEY:
        print("Erreur : SENDGRID_API_KEY manquante sur Render.")
        return False

    encoded_pdf = base64.b64encode(pdf_content).decode()

    # Liste des destinataires (Modifie l'adresse ici si besoin)
    destinataires = [
        {"email": "xavier.oliere@alyzia.com"}
    ]

    payload = {
        "personalizations": [{"to": destinataires}],
        "from": {"email": "alyzia.cdg2@gmail.com", "name": "SIA - CDG STATION"},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}],
        "attachments": [{
            "content": encoded_pdf,
            "filename": filename,
            "type": "application/pdf",
            "disposition": "attachment"
        }]
    }

    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://api.sendgrid.com/v3/mail/send",
            json=payload,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
        )
        return r.status_code < 400

# --- ROUTES ---

@app.get("/")
async def read_index():
    # Affiche le menu d'accueil index.html par défaut
    return FileResponse('index.html')

@app.post("/send-pdf")
async def send_pdf(
    pdf: UploadFile = File(...),
    filename: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...)
):
    try:
        # 1. On lit le contenu binaire du fichier reçu
        pdf_content = await pdf.read()
        
        # 2. On vérifie que le fichier n'est pas vide
        if not pdf_content:
            return JSONResponse(status_code=400, content={"status": "error", "message": "Fichier PDF vide"})

        # 3. On appelle l'envoi avec le contenu binaire
        success = await envoyer_email_sendgrid(pdf_content, filename, subject, body)
        
        if success:
            return {"status": "success"}
        else:
            return JSONResponse(status_code=500, content={"status": "error", "message": "Échec de l'envoi SendGrid"})
            
    except Exception as e:
        print(f"Erreur serveur : {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

# Montage des fichiers statiques (Sert HTML, CSS, Images depuis la racine ".")
# html=True permet de trouver automatiquement les fichiers .html
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    # Render utilise souvent le port 10000 par défaut
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)