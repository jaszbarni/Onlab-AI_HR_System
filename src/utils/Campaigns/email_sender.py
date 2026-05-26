import smtplib
import os
import streamlit as st
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from Database.db_login import generate_user_token
from Database.db_employee import get_user_by_email



def email_sender(filler_employee):

    if "user" in st.session_state and st.session_state.user:
        employee_data = get_user_by_email(st.session_state.user.email)
        if employee_data and employee_data.get("email_password"):
            SENDER_EMAIL = employee_data["email"]
            SENDER_PASSWORD = employee_data["email_password"]
        else:
            st.error("❌ No email password is set. Please set up your email password first.")
            return False
    else:
        st.error("❌ Failed to send email. User not logged in.")
        return False

    url = "http://localhost:8501"
    token = generate_user_token(filler_employee.get("id"))

    body = f"""
            Hi {filler_employee.get("first_name")},
            Please fill out the forms that are assigned to you.
            Click the following link to fill out: {url}/?token={token}
            Thank you!
            HR team"""

    message = MIMEMultipart()
    message["from"] = f"HR System <{SENDER_EMAIL}>"
    message["to"] = filler_employee.get("email")
    message["subject"] = "Employee review"

    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(host="smtp.gmail.com", port=587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(message)
        return True
    except Exception as e:
        st.error(f"❌ Failed to send email: {e}")
        return False
