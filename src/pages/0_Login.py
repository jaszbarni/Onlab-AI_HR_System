import streamlit as st
import re
from utils.common import setup_page
from database_manager import (
    authenticate_employee,
    is_employee_registered,
    has_employee_password,
)
from classes.user_class import User

setup_page()

st.header("Employee Login", text_alignment="center")
st.markdown("---")
col1, col2, col3 = st.columns([1, 2.5, 1])
# Initialize login attempt tracking
with col2:
    if "login_attempts" not in st.session_state:
        st.session_state.login_attempts = {}

    def is_valid_email(email: str) -> bool:
        """Validate email format."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    st.subheader("Login to Your Account")
    
    #TODO kiszedni
    """ email = st.text_input(
        "Email",
        placeholder="your.email@example.com",
        key="login_email"
    ) """
    email = "leader@example.com"

    """ password = st.text_input(
        "Password",
        type="password",
        key="login_password"
    ) """

    password = "asd"
    
    if st.button("Login", type="primary", use_container_width=True):
        email = email.strip().lower()
        
        # Validation
        if not email or not password:
            st.error("❌ Please enter both email and password")
        elif not is_valid_email(email):
            st.error("❌ Please enter a valid email address")
        else:
            # Check if employee exists
            if not is_employee_registered(email):
                st.error("❌ Email not found in system")
            # If employee has no password set, allow default password "1234"
            elif not has_employee_password(email) and password == "1234":
                user = is_employee_registered(email)
                # Get employee data for session
                from database_manager import get_user_by_email
                employee_data = get_user_by_email(email)
                if employee_data:
                    st.session_state.user = User(
                        employee_data["first_name"],
                        employee_data["last_name"],
                        employee_data["email"],
                        employee_data["position"]
                    )
                    st.success(f"Welcome, {employee_data['first_name']}!")
                    st.balloons()
                    st.rerun()
            # Otherwise, authenticate with password
            else:
                user = authenticate_employee(email, password)
                
                if user:
                    st.session_state.user = user
                    st.success(f"✅ Welcome, {user.first_name}!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Invalid email or password")

   