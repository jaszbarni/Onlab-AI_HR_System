import streamlit as st
from database_manager import get_all_employees, update_employee_role, ROLES, check_permission, delete_employee, update_employee_group

st.set_page_config(layout="wide")

try:
    with open("Resources/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.error("CSS file not found. Please make sure 'form.css' is in the same folder.")

st.title("Permissions", text_alignment="center")

# Initialize session state for edit mode
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = {}

employees = get_all_employees()
st.subheader("Employees")

col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
with col1:
    st.caption("**ID**", text_alignment="left")
with col2:
    st.caption("**Name**", text_alignment="left")
with col3:
    st.caption("**Email**", text_alignment="left")
with col4:
    st.caption("**Group**", text_alignment="left")
if check_permission("update"):
    with col5:
        st.caption("**Edit**", text_alignment="left")
with col6:
    st.caption("**Role**", text_alignment="center")

if employees:
    for employee in employees:
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        with col1:
            st.write(f"{employee['id']}")
        with col2:
            st.write(f"**{employee['first_name']} {employee['last_name']}**")
        with col3:
            st.write(employee['email'])
        with col4:
            # Check if in edit mode for this employee
            if st.session_state.edit_mode.get(employee['id'], False):
                new_group = st.text_input("Group", value=employee['group'], key=f"group_{employee['id']}", label_visibility="collapsed")
                if new_group != employee['group']:
                    update_employee_group(employee['id'], new_group)
                    st.session_state.edit_mode[employee['id']] = False
                    st.rerun()
            else:
                st.write(employee['group'])
        if check_permission("update"):
            with col5:
                if st.button(label="✏️", key=f"edit_{employee['id']}"):
                    st.session_state.edit_mode[employee['id']] = not st.session_state.edit_mode.get(employee['id'], False)
                    st.rerun()
        with col6:
            disabled = True
            if check_permission("update"):
                disabled = False

            new_role = st.selectbox(
                "Role",
                options=list(ROLES.keys()),
                index=list(ROLES.keys()).index(employee['role']),
                key=f"role_{employee['id']}",
                label_visibility="collapsed",
                disabled=disabled
            )
            if new_role != employee['role']:
                update_employee_role(employee['id'], new_role)
                st.rerun()
        if check_permission("delete"):
            with col7:
                st.button(label="❌", key=f"delete_{employee['id']}", on_click=delete_employee, args=(employee['id']))


else:
    st.info("No employees found.")
