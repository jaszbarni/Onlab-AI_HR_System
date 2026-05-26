import streamlit as st
import time
from Database.db_employee import get_user_by_email, update_employee_email_password
from Database.db_login import set_employee_password

 
st.subheader("Set Up Your Account Password")
col1, col2, col3 = st.columns([1, 2.5, 1])

with col2:
    new_password = st.text_input(
        "New Password",
        type="password",
        key="setup_password",
        help="Use a strong password with at least 8 characters"
    )
    confirm_password = st.text_input(
        "Confirm Password",
        type="password",
        key="setup_confirm_password"
    )

    if st.button("Set Password", type="primary", use_container_width=True):
        
        if len(new_password) < 8:
            st.error("❌ Password must be at least 8 characters long")
        elif new_password != confirm_password:
            st.error("❌ Passwords do not match")
        else:
            # Check if user exists
            current_user = st.session_state.get("user")
            
            if current_user:
                employee_dict = get_user_by_email(current_user.email)
                # Set the password
                if employee_dict and set_employee_password(employee_dict["id"], new_password):
                    st.success("✅ Password set successfully! You can now log in.")
                    time.sleep(1.5) # Give the user time to read the success message
                    st.rerun()
                else:
                    st.error("❌ Error setting password. Please try again.")
            else:
                st.error("❌ Email not found in system. Please contact your administrator.")


st.subheader("Set up your email password ")
col1, col2 = st.columns([3, 1])
with col1:
    st.info("This is your emails password, this is necessary to send automatic emails, please get an app password in this link: ")
with col2:
    st.link_button("link", "https://myaccount.google.com/apppasswords?pli=1&rapt=AEjHL4PJ560QxAlmA7ENoPA6iZ824KmNWPz_NfBjCpUU5DN-CgDv-X5rf8knwizfGPDj1O-uss342AaahS4eI4w13XlAM34BiWw-CzI-iCw0BLxspku4y8Y")

col1, col2, col3 = st.columns([1, 2.5, 1])
with col2:
    email_password = st.text_input(
        "Email Password",
        type="password",
        key="email_password"
    )

    if st.button("Save Email Password", type="primary", use_container_width=True):
        if not email_password:
            st.error("❌ Email password cannot be empty")
        else:
            current_user = st.session_state.get("user")
            if current_user:
                employee_dict = get_user_by_email(current_user.email)
                if employee_dict and update_employee_email_password(employee_dict["id"], email_password):
                    st.success("✅ Email password saved successfully!")
                else:
                    st.error("❌ Error saving email password. Please try again.")
            else:
                st.error("❌ Email not found in system. Please contact your administrator.")