import os
import base64
import resend

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# CORS
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

# Clé Resend
resend.api_key = os.environ.get("RESEND_API_KEY")


# ========= ENVOI EMAIL =========
async def envoyer_email(pdf_content, filename, subject, body):

    params = {
        "from": "ALYZIA DOCS <onboarding@resend.dev>",
        "to": ["xavier.oliere@alyzia.com"],
        "subject": subject,
        "text": body,
        "attachments": [
            {
                "filename": filename,
                "content": base64.b64encode(pdf_content).decode()
            }
        ]
    }

    response = resend.Emails.send(params)

    print("RESEND RESPONSE :", response)

    return True


# ========= PAGE ACCUEIL =========
@app.get("/")
async def home():
    return FileResponse("index.html")


# ========= ROUTE ENVOI PDF =========
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
                content={
                    "status": "error",
                    "message": "PDF vide"
                }
            )

        await envoyer_email(
            pdf_content,
            filename,
            subject,
            body
        )

        return {
            "status": "success"
        }

    except Exception as e:

        print("ERREUR :", e)

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        )


# ========= FICHIERS HTML =========
app.mount("/", StaticFiles(directory=".", html=True), name="static")
