import streamlit as st
from classes.user_class import User
from Database.login import get_user_by_token, has_employee_password
from Database.database_manager import check_permission


#TODO login

st.set_page_config(layout="wide", initial_sidebar_state="expanded")

try:
    with open("Resources/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.error("CSS file not found. Please make sure 'form.css' is in the same folder.")

# Hide the sidebar collapse/expand buttons to fix it open
# Also hide the "Change Password" tab from the sidebar navigation
st.markdown(
    """
    <style>
        [data-testid="collapsedControl"] {display: none;}
        [data-testid="stSidebarCollapseButton"] {display: none;}
        [data-testid="stSidebarNavItems"] li:has(a[href$="change_password"]) {
            display: none !important;
        }
        [data-testid="stSidebarNavItems"] a[href$="change_password"] {
            display: none !important;
        }
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
    pages.append(st.Page("pages/0_Login.py", title="Login"))
    
if "user" in st.session_state:
    pages.append(st.Page("pages/7_change_password.py", title="Change Password", url_path="change_password"))
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
        
        st.divider()
        
        if st.button("Change password", use_container_width=True):
            st.switch_page("pages/7_change_password.py")

        if st.button("Logout", type="primary"):
            del st.session_state.user
            st.rerun()


st.title("HR System", text_alignment="center")
if "user" in st.session_state:
    if not has_employee_password(st.session_state.user.email):
        st.error("Change the password now!")


#st.button("Delete all forms", on_click=delete_all_forms())

#st.json({k: str(v) for k, v in st.session_state.items()})


page.run()
