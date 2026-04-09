import streamlit as st
from database_manager import add_employee, generate_user_token, get_all_employees
from classes.user_class import User
from utils.common import setup_page, initialize_session_state

setup_page()
# Removed check_user_initialized() so you can generate a link without being logged in!
initialize_session_state("link_generator", "current_form_id")

url = "http://localhost:8501"

if st.session_state.link_generator:
    st.header("Generate Login Link")
    
    # Dynamically fetch all employees to avoid hardcoding
    all_employees = get_all_employees()
    
    if all_employees:
        # Map display name (including position) to the employee ID to handle duplicates properly
        employee_options = {f"{emp['first_name']} {emp['last_name']} - Position: {emp['position']} ({emp['email']})": emp["id"] for emp in all_employees}
        selected_label = st.selectbox("Select user to generate a link for:", list(employee_options.keys()))

        if st.button("Generate Link", type="primary"):
            selected_id = employee_options[selected_label]
            token = generate_user_token(selected_id)
            st.info(f"Your login link: {url}/?token={token}")
    else:
        st.warning("No employees found in the database. Add them below.")
        
    st.divider()

    # Keep the original employee creation logic
    st.subheader("Test Data Generation")
    test_F = User("Teszt", "Elek", "leader@example.com", "Vezető")
    test_BO = User("Teszt", "Jóska", "testjoska@example.com", "Back office")
    test_M = User("Teszt", "Péter", "testpeter@example.com", "Manager")
    test_V = User("Teszt", "Vilmos", "testvilmos@example.com", "Fizikai")
    if st.button("Add test employees"):
        add_employee(test_BO)
        add_employee(test_F)
        add_employee(test_M)
        add_employee(test_V)
        st.rerun()
