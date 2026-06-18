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

MAIL_FROM = "alyzia.cdg2@gmail.com"
MAIL_TO = "xavier.oliere@alyzia.com"


def envoyer_email_brevo(pdf_content, filename, subject, body):
    brevo_login = os.environ.get("BREVO_LOGIN")
    brevo_password = os.environ.get("BREVO_PASSWORD")

    if not brevo_login or not brevo_password:
        raise Exception("BREVO_LOGIN ou BREVO_PASSWORD manquant dans Render")

    msg = EmailMessage()
    msg["From"] = MAIL_FROM
    msg["To"] = MAIL_TO
    msg["Subject"] = subject
    msg.set_content(body)

    msg.add_attachment(
        pdf_content,
        maintype="application",
        subtype="pdf",
        filename=filename
    )

    with smtplib.SMTP("smtp-relay.brevo.com", 587, timeout=30) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(brevo_login, brevo_password)
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

        envoyer_email_brevo(pdf_content, filename, subject, body)

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
