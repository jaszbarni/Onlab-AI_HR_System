import streamlit as st
from database_manager import add_employee
from classes.user_class import User


#TODO Jogosultságok kezelése, login

st.set_page_config(layout="wide")

try:
    with open("Resources/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.error("CSS file not found. Please make sure 'form.css' is in the same folder.")


# Felhasználó inicializálása (Hardcoded)
# Ez a rész később lecserélhető az st.login() hívásra
test_F = User("Teszt", "Elek", "leader@example.com", "")
test_BO = User("Teszt", "Jóska", "testjoska@example.com", "")
test_M = User("Teszt", "Péter", "testpeter@example.com", "")
test_V = User("Teszt", "Vilmos", "testvilmos@example.com", "")

st.session_state.user = test_V

if st.button("Add test employees"):
    add_employee(test_BO)
    add_employee(test_F)
    add_employee(test_M)
    add_employee(test_V)
    st.rerun()



# Configure sidebar navigation (excludes 4_EditForm from sidebar)
pages = [
    st.Page("pages/1_Employees.py", title="Employees"),
    st.Page("pages/2_Campaigns.py", title="Campaigns"),
    st.Page("pages/3_Forms.py", title="Forms"),
]

page = st.navigation(pages)

# Sidebar-on megjelenítjük a bejelentkezett felhasználót
with st.sidebar:
    st.header("User Data")
    st.write(f"Name: {st.session_state.user.first_name} {st.session_state.user.last_name}")
    st.write(f"Role: {st.session_state.user.role}")


st.title("HR System", text_alignment="center")

page.run()