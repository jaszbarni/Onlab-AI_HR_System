import streamlit as st
import pandas as pd
from database_manager import get_all_employees

st.set_page_config(layout="wide")

try:
    with open("Resources/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.error("CSS file not found. Please make sure 'form.css' is in the same folder.")

st.title("Permissions", text_alignment="center")

employees = get_all_employees()
st.subheader("Employees")

st.table(employees)
