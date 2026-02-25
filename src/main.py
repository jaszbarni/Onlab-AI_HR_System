import streamlit as st
from database_manager import User, add_employee


st.set_page_config(layout="wide")

try:
    with open("Resources/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.error("CSS file not found. Please make sure 'form.css' is in the same folder.")


# Felhasználó inicializálása (Hardcoded)
# Ez a rész később lecserélhető az st.login() hívásra
test_user = User("Teszt", "Elek", "Leader", "leader@example.com", "")

st.session_state.user = test_user

#add_employee(test_user)

if "user" not in st.session_state:
    st.session_state.user = test_user


# Sidebar-on megjelenítjük a bejelentkezett felhasználót
with st.sidebar:
    st.header("Felhasználó adatok")
    st.write(f"Name: {st.session_state.user.first_name} {st.session_state.user.last_name}")
    st.write(f"Role: {st.session_state.user.role}")


st.title("HR System", text_alignment="center")

if st.button(label="Permission manager", width="content", icon_position="right", type="secondary"):
    st.switch_page("pages/1_Permissions.py")
if st.button(label="Form templates", width="content", icon_position="right", type="secondary"):
    st.switch_page("pages/3_Forms.py")