# Import smtplib for the actual sending function
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "jaszbarni444@gmail.com")
# NOTE: Use a Gmail App Password here, not your standard account password!
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "qrpg ggld brjy abyn")

body = "Hello there"

message = MIMEMultipart()
message["from"] = f"HR System <{SENDER_EMAIL}>"
message["to"] = "seaislefewhtrqboly@onldm.net"
message["subject"] = "Employee review"

message.attach(MIMEText(body, "plain"))

with smtplib.SMTP(host="smtp.gmail.com", port=587) as server:
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.send_message(message)

print("Email sent!")