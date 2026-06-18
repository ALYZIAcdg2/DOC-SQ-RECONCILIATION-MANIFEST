import os
import base64
import httpx
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://alyziacdg2.github.io",
        "https://doc-sq.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def envoyer_email_sendgrid(pdf_content, filename, subject, body):
    api_key = os.environ.get("SENDGRID_API_KEY")

    if not api_key:
        print("Erreur : SENDGRID_API_KEY manquante sur Render.")
        return False

    encoded_pdf = base64.b64encode(pdf_content).decode()

    payload = {
        "personalizations": [
            {"to": [{"email": "xavier.oliere@alyzia.com"}]}
        ],
        "from": {
            "email": "alyzia.cdg2@gmail.com",
            "name": "ALYZIA DOCS SQ"
        },
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": body}
        ],
        "attachments": [
            {
                "content": encoded_pdf,
                "filename": filename,
                "type": "application/pdf",
                "disposition": "attachment"
            }
        ]
    }

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            "https://api.sendgrid.com/v3/mail/send",
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )

        print("SENDGRID STATUS:", r.status_code)
        print("SENDGRID RESPONSE:", r.text)

        return r.status_code < 400


@app.get("/")
async def read_index():
    return FileResponse("index.html")


@app.post("/send-pdf")
async def send_pdf(
    pdf: UploadFile = File(...),
    filename: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...)
):
    try:
        pdf_content = await pdf.read()

        if not pdf_content:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Fichier PDF vide"}
            )

        success = await envoyer_email_sendgrid(
            pdf_content,
            filename,
            subject,
            body
        )

        if success:
            return {"status": "success"}

        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Échec de l'envoi SendGrid"}
        )

    except Exception as e:
        print("Erreur serveur :", e)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


app.mount("/", StaticFiles(directory=".", html=True), name="static")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
