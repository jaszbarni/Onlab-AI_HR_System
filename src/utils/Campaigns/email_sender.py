import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from database_manager import generate_user_token


def email_sender(filler_employee):
    SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "jaszbarni444@gmail.com")
    SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "qrpg ggld brjy abyn")

    url = "http://localhost:8501"
    token = generate_user_token(filler_employee.get("id"))

    body = f"""Please fill out the forms that are assigned to you.
            Click the following link to fill out: {url}/?token={token}
            Thank you!
            HR team"""

    message = MIMEMultipart()
    message["from"] = f"HR System <{SENDER_EMAIL}>"
    message["to"] = filler_employee.get("email")
    message["subject"] = "Employee review"

    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(host="smtp.gmail.com", port=587) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(message)
        
