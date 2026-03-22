import streamlit as st
from utils.common import setup_page, check_user_initialized, initialize_session_state
from utils.template_views import show_templates_list, show_edit_template

# Setup
setup_page()
check_user_initialized()
initialize_session_state("form_templates_view", "current_form_id")

# Main routing
if st.session_state.forms_view == "list":
    show_templates_list()
elif st.session_state.forms_view == "edit_template":
    show_edit_template()
