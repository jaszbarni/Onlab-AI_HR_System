import streamlit as st

st.set_page_config(layout="wide")

try:
    with open("form.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.error("CSS file not found. Please make sure 'form.css' is in the same folder.")

st.title("Permissions", text_alignment="center")