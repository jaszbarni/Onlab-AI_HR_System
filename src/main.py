import streamlit as st
from database_manager import add_employee, delete_all_forms, get_user_by_token, generate_user_token, delete_all_employees, check_permission
from classes.user_class import User


#TODO login

st.set_page_config(layout="wide", initial_sidebar_state="expanded")

try:
    with open("Resources/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.error("CSS file not found. Please make sure 'form.css' is in the same folder.")

# Hide the sidebar collapse/expand buttons to fix it open
st.markdown(
    """
    <style>
        [data-testid="collapsedControl"] {display: none;}
        [data-testid="stSidebarCollapseButton"] {display: none;}
    </style>
    """,
    unsafe_allow_html=True,
)

# Magic Link Login Logic
if "token" in st.query_params:
    token = st.query_params["token"]
    user = get_user_by_token(token)
    if user:
        st.session_state.user = user
        # Clear the token from the URL for cleanliness and security
        del st.query_params["token"]
    else:
        st.error("Invalid or expired login link.")
        st.stop()
        
#st.button("Delete all employees", on_click=delete_all_employees)

pages = []

if "user" not in st.session_state:
    pages.append(st.Page("pages/5_Generate_link.py", title="Generate link"))

if "user" in st.session_state:
    pages.insert(0, st.Page("pages/4_Forms.py", title="Forms"))
    
    # Management pages require 'read' permission (Back office, Manager, Vezető)
    if check_permission("read"):
        pages.insert(0, st.Page("pages/6_AI_review.py", title="AI Review"))
        pages.insert(0, st.Page("pages/3_Form_Templates.py", title="Form Templates"))
        pages.insert(0, st.Page("pages/2_Campaigns.py", title="Campaigns"))
        pages.insert(0, st.Page("pages/1_Employees.py", title="Employees"))



page = st.navigation(pages)

# Sidebar-on megjelenítjük a bejelentkezett felhasználót
if "user" in st.session_state:
    with st.sidebar:
        st.header("User Data")
        st.write(f"Name: {st.session_state.user.first_name} {st.session_state.user.last_name}")
        st.write(f"Position: {st.session_state.user.position}")
        
        if st.button("Logout"):
            del st.session_state.user
            st.rerun()


st.title("HR System", text_alignment="center")
#st.button("Delete all forms", on_click=delete_all_forms())

#st.json({k: str(v) for k, v in st.session_state.items()})


page.run()
