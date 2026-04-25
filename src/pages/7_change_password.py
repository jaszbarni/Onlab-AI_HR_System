import streamlit as st

from database_manager import  set_employee_password, get_user_by_email

st.subheader("Set Up Your Password")
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
        
        if len(new_password) < 0: #TODO
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
                    st.rerun()
                else:
                    st.error("❌ Error setting password. Please try again.")
            else:
                st.error("❌ Email not found in system. Please contact your administrator.")
