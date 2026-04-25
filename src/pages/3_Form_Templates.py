import streamlit as st
from utils.common import setup_page, check_user_initialized, initialize_session_state
from utils.Form_templates.template_views import show_templates_list, show_edit_template

# Setup
setup_page()
check_user_initialized()
initialize_session_state("forms_view", "current_form_id")

# Main routing
with st.spinner("Loading..."):
    if st.session_state.forms_view == "list":
        show_templates_list()
    elif st.session_state.forms_view == "edit_template":
        show_edit_template()
