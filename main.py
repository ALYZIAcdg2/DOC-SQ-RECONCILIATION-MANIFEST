import os
import smtplib
from email.message import EmailMessage

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

GMAIL_FROM = "alyzia.cdg2@gmail.com"
GMAIL_TO = "xavier.oliere@alyzia.com"


def envoyer_email_gmail(pdf_content, filename, subject, body):
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")

    if not gmail_password:
        raise Exception("GMAIL_APP_PASSWORD manquant dans Render")

    msg = EmailMessage()
    msg["From"] = GMAIL_FROM
    msg["To"] = GMAIL_TO
    msg["Subject"] = subject

    msg.set_content(body)

    msg.add_attachment(
        pdf_content,
        maintype="application",
        subtype="pdf",
        filename=filename
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL_FROM, gmail_password)
        smtp.send_message(msg)


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

        envoyer_email_gmail(
            pdf_content,
            filename,
            subject,
            body
        )

        return {"status": "success"}

    except Exception as e:
        print("ERREUR EMAIL :", e)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


app.mount("/", StaticFiles(directory=".", html=True), name="static")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
