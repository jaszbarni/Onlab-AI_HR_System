import streamlit as st
from utils.common import setup_page, check_user_initialized, initialize_session_state
from utils.form_views import show_list_view, show_form_fill_view


setup_page()
check_user_initialized()
initialize_session_state("forms_view", "current_form_id", "current_assignment_id", "current_target_name")

with st.spinner("Loading..."):
    if st.session_state.forms_view == "list":
        show_list_view("forms_view", "current_form_id")
    elif st.session_state.forms_view == "fill":
        show_form_fill_view("forms_view", "current_form_id")
