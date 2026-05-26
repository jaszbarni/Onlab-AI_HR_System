"""Common utilities and setup functions for all pages."""
import re

import streamlit as st


@st.cache_data
def load_css():
    """Load CSS once and cache it."""
    try:
        with open("Resources/style.css") as f:
            return f.read()
    except FileNotFoundError:
        return None


def invalidate_cache():
    """Clear Streamlit cache when data is modified."""
    st.cache_data.clear()


def setup_page():
    """Initialize page configuration and styling."""
    st.set_page_config(layout="wide", initial_sidebar_state="expanded")
    
    css_content = load_css()
    if css_content:
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    else:
        st.error("CSS file not found. Please make sure 'style.css' is in the same folder.")

    # Hide the sidebar collapse/expand buttons to fix it open
    st.markdown(
        """
        <style>
            [data-testid="collapsedControl"] {display: none;}
            [data-testid="stSidebarCollapseButton"] {display: none;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def check_user_initialized():
    """Check if user is initialized, stop if not."""
    if "user" not in st.session_state:
        st.error("User not initialized. Please go back to the main page.")
        st.stop()


def set_state(**kwargs):
    """Set session state and query params, then rerun to support back button."""
    for k, v in kwargs.items():
        st.session_state[k] = v
        if v is None:
            if k in st.query_params:
                del st.query_params[k]
        else:
            st.query_params[k] = str(v)
    st.rerun()


def get_user_name():
    """Get full name of current user."""
    return f"{st.session_state.user.first_name} {st.session_state.user.last_name}"


def get_user_permission_cached(permission):
    """Check permission with session-level caching (avoids repeated DB queries).
    
    Args:
        permission: The permission to check (e.g., 'read', 'create', 'update', 'delete')
        
    Returns:
        bool: True if user has the permission, False otherwise
    """
    # Use session state cache for permission checks
    cache_key = f"_perm_{permission}"
    
    if cache_key not in st.session_state:
        # Import here to avoid circular imports
        from Database.db_database_manager import check_permission
        st.session_state[cache_key] = check_permission(permission)
    
    return st.session_state[cache_key]


def initialize_session_state(*keys):
    """Initialize session state variables for view management.
    
    Args:
        *keys: Variable number of session state keys to initialize
               First key defaults to "list", others default to None
    """
    # Remove query params not in keys to prevent leaking across pages
    for q_key in list(st.query_params.keys()):
        if q_key not in keys and q_key != "token":
            del st.query_params[q_key]
            
    for i, key in enumerate(keys):
        default_val = "list" if i == 0 else None
        
        if key in st.query_params:
            val = st.query_params[key]
            if val == "None":
                val = None
            elif val.isdigit():
                val = int(val)
            st.session_state[key] = val
        else:
            # The parameter is missing from the URL (user navigated back or fresh load).
            # Force session state to match this reality.
            st.session_state[key] = default_val
            
            # Sync back to URL if it's the primary view key to ensure clean URLs
            if default_val is not None:
                st.query_params[key] = str(default_val)


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
        set_state(**{view_key: target_view, form_id_key: None})
        return True
    return False

@st.dialog("Confirm Deletion")
def delete_confirmation_dialog(item_name, delete_callback, *args):
    """
    A true modal popup for deletions.
    Args:
        item_name: Name of the item to display
        delete_callback: The function to run if confirmed (e.g., delete_campaign)
        args: Any arguments needed for the callback (e.g., item_id)
    """
    st.write(f"Are you sure you want to delete **{item_name}**?")
    st.warning("This action cannot be undone.")
    
    col1, col2 = st.columns(2)
    if col1.button("Delete", type="primary", use_container_width=True):
        delete_callback(*args)
        st.success(f"Deleted {item_name}")
        st.rerun()
        
    if col2.button("Cancel", use_container_width=True):
        st.rerun()

def check_email_format(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))