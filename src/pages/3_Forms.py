import streamlit as st
from database_manager import (
    get_all_forms, create_form, delete_form, check_permission
)

st.set_page_config(layout="wide")

try:
    with open("Resources/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.error("CSS file not found. Please make sure 'style.css' is in the same folder.")

# Check if user is initialized
if "user" not in st.session_state:
    st.error("User not initialized. Please go back to the main page.")
    st.stop()

st.title("Form templates", text_alignment="center")

# Add new form button
col1, col2 = st.columns([0.8, 0.2])
with col2:
    if st.button(label="➕ Add new form", use_container_width=True):
        st.session_state.new_form = True
        st.switch_page("pages/4_EditForm.py")

st.divider()

# Display existing forms
forms = get_all_forms()

if not forms:
    st.info("No forms created yet. Click 'Add new form' to create one.")
else:
    st.subheader(f"Existing Forms ({len(forms)})")
    
    for form in forms:
        form_id, name, description, created_by, created_date = form
        
        with st.container(border=True):
            col1, col2, col3 = st.columns([0.7, 0.15, 0.15])
            
            with col1:
                st.markdown(f"### {name}")
                if description:
                    st.caption(description)
            
            with col2:
                if st.button("Edit", key=f"edit_{form_id}", use_container_width=True):
                    st.session_state.edit_form_id = form_id
                    st.switch_page("pages/4_EditForm.py")
            
            with col3:
                if st.button("Delete", key=f"delete_{form_id}", use_container_width=True):
                    delete_form(form_id)
                    st.rerun()