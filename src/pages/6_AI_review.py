import streamlit as st
from utils.common import setup_page, check_user_initialized, initialize_session_state
from utils.AI_review.AI_review import employee_list_view, review_view


# Setup

setup_page()
check_user_initialized()
initialize_session_state("review_view", "current_employee_id")

# Main routing
if st.session_state.review_view == "list":
    employee_list_view()
elif st.session_state.review_view == "review":
    review_view()