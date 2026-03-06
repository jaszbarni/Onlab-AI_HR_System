"""Common utilities and setup functions for all pages."""
import streamlit as st


def setup_page():
    """Initialize page configuration and styling."""
    st.set_page_config(layout="wide")
    
    try:
        with open("Resources/style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error("CSS file not found. Please make sure 'style.css' is in the same folder.")


def check_user_initialized():
    """Check if user is initialized, stop if not."""
    if "user" not in st.session_state:
        st.error("User not initialized. Please go back to the main page.")
        st.stop()


def get_user_name():
    """Get full name of current user."""
    return f"{st.session_state.user.first_name} {st.session_state.user.last_name}"


def initialize_session_state(*keys):
    """Initialize session state variables for view management.
    
    Args:
        *keys: Variable number of session state keys to initialize
               First key defaults to "list", others default to None
    """
    for i, key in enumerate(keys):
        if key not in st.session_state:
            # First key (view_key) defaults to "list", others default to None
            st.session_state[key] = "list" if i == 0 else None


def back_button(view_key, form_id_key, target_view="list"):
    """Create and handle a back button.
    
    Args:
        view_key: Session state key for current view
        form_id_key: Session state key for current form ID
        target_view: View to return to (default: "list")
        
    Returns:
        bool: True if button was clicked
    """
    if st.button("← Back"):
        st.session_state[view_key] = target_view
        st.session_state[form_id_key] = None
        st.rerun()
        return True
    return False
