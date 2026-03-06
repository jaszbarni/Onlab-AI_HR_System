import streamlit as st
from utils.common import setup_page, check_user_initialized, initialize_session_state
from utils.campaigns_views import (
    show_campaigns_list, show_create_campaign, show_edit_campaign,
    show_campaign_forms, show_create_form, show_edit_form
)
from utils.matrix import show_assign_group


# Setup
setup_page()
check_user_initialized()
initialize_session_state("campaigns_view", "current_campaign_id", "current_form_id")

# Route to appropriate view
if st.session_state.campaigns_view == "list":
    show_campaigns_list()
elif st.session_state.campaigns_view == "create_campaign":
    show_create_campaign()
elif st.session_state.campaigns_view == "edit_campaign":
    show_edit_campaign()
elif st.session_state.campaigns_view == "campaign_forms":
    show_campaign_forms()
elif st.session_state.campaigns_view == "create_form":
    show_create_form(st.session_state.current_campaign_id)
elif st.session_state.campaigns_view == "edit_form":
    show_edit_form(st.session_state.current_campaign_id)
elif st.session_state.campaigns_view == "assign_group":
    show_assign_group(st.session_state.current_form_id)


