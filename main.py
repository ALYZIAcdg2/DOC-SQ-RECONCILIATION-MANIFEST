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

MAIL_FROM = "alyzia.cdg2@gmail.com"
MAIL_FROM_NAME = "ALYZIA DOCS SQ"
MAIL_TO = "xavier.oliere@alyzia.com"


async def envoyer_email_brevo_api(pdf_content, filename, subject, body):
    api_key = os.environ.get("BREVO_API_KEY")

    if not api_key:
        raise Exception("BREVO_API_KEY manquant dans Render")

    payload = {
        "sender": {
            "name": MAIL_FROM_NAME,
            "email": MAIL_FROM
        },
        "to": [
            {
                "email": MAIL_TO
            }
        ],
        "subject": subject,
        "textContent": body,
        "attachment": [
            {
                "name": filename,
                "content": base64.b64encode(pdf_content).decode("utf-8")
            }
        ]
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://api.brevo.com/v3/smtp/email",
            json=payload,
            headers={
                "api-key": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )

    print("BREVO API STATUS:", response.status_code)
    print("BREVO API RESPONSE:", response.text)

    if response.status_code >= 400:
        raise Exception(f"Brevo API error {response.status_code}: {response.text}")

    return True


@app.get("/")
async def home():
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
                content={"status": "error", "message": "PDF vide"}
            )

        await envoyer_email_brevo_api(
            pdf_content,
            filename,
            subject,
            body
        )

        return {"status": "success"}

    except Exception as e:
        import traceback
        print("ERREUR EMAIL :", repr(e))
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


app.mount("/", StaticFiles(directory=".", html=True), name="static")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
