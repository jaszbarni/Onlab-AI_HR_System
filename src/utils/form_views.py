"""Views for form filling and submission."""
import streamlit as st
from database_manager import get_all_forms, get_forms_for_user_by_email
from classes.form_template_class import FormTemplate
from utils.common import get_user_name, back_button


def render_question_input(question_id, question_text, question_type, min_val, max_val):
    """Render an input field for a question.
    
    Args:
        question_id: ID of the question
        question_text: Text of the question
        question_type: Type of question (Text Box, Rating, etc.)
        min_val: Minimum value for ratings
        max_val: Maximum value for ratings
        
    Returns:
        The user's answer
    """
    key = f"answer_{question_id}"
    
    # Initialize session state
    if key not in st.session_state:
        if question_type in ["0-5 Rating", "1-10 Rating"]:
            st.session_state[key] = min_val if min_val is not None else 0
        else:
            st.session_state[key] = ""
    
    st.markdown(f"**{question_text}**")
    
    if question_type == "Text Box":
        answer = st.text_area("", key=key, height=100)
    elif question_type == "0-5 Rating":
        answer = st.slider("", min_value=0, max_value=5, value=st.session_state[key], key=key)
    elif question_type == "1-10 Rating":
        answer = st.slider("", min_value=1, max_value=10, value=st.session_state[key], key=key)
    elif question_type == "Multiple Choice":
        answer = st.text_input("Enter your choice:", key=key)
    else:
        answer = st.text_input("", key=key)
    
    return answer


def show_list_view(view_key, form_id_key):
    """Display list of available forms for users to fill out.
    
    Args:
        view_key: Session state key for current view
        form_id_key: Session state key for current form ID
    """
    st.header("Forms", text_alignment="left")
    st.divider()

    user_email = st.session_state.user.email
    forms = get_forms_for_user_by_email(user_email)
    user_name = get_user_name()

    if not forms:
        st.info("No forms assigned to you at the moment.")
    else:
        st.subheader(f"Available Forms ({len(forms)})")
        
        for form in forms:
            form_id, name, description, created_by, created_date = form
            form_template = FormTemplate(form_id)
            user_has_submitted = form_template.has_user_submitted(user_name)
            
            with st.container(border=True):
                col1, col2 = st.columns([0.85, 0.15])
                
                with col1:
                    st.markdown(f"### {name}")
                    if description:
                        st.caption(description)
                    if user_has_submitted:
                        st.caption("✓ You have already submitted this form")
                
                with col2:
                    if user_has_submitted:
                        st.button("✓ Completed", key=f"fillout_{form_id}", use_container_width=True, disabled=True)
                    else:
                        if st.button("📝 Fill Out", key=f"fillout_{form_id}", use_container_width=True):
                            st.session_state[view_key] = "fill"
                            st.session_state[form_id_key] = form_id
                            st.rerun()


def show_form_fill_view(view_key, form_id_key):
    """Display form for user to fill out and submit.
    
    Args:
        view_key: Session state key for current view
        form_id_key: Session state key for current form ID
    """
    form_id = st.session_state[form_id_key]
    user_name = get_user_name()
    
    if not form_id:
        st.error("No form selected.")
        back_button(view_key, form_id_key)
        return
    
    # Load form
    form = FormTemplate(form_id)
    form_info = form.get_form_info()
    
    if not form_info:
        st.error("Form not found.")
        back_button(view_key, form_id_key)
        return
    
    # Check if user has already submitted
    if form.has_user_submitted(user_name):
        st.warning("You have already submitted this form. Each user can only submit a form once.")
        back_button(view_key, form_id_key)
        return
    
    # Back button
    back_button(view_key, form_id_key)
    st.divider()
    
    # Display form header
    st.title(form.get_name())
    if form.get_description():
        st.write(form.get_description())
    
    st.divider()
    
    # Check if form has questions
    if not form.has_questions():
        st.info("This form has no questions yet.")
        return
    
    # Render form questions
    answers = {}
    questions = form.get_questions()
    
    for question in questions:
        question_id, question_text, question_type, min_val, max_val, order = question
        answer = render_question_input(question_id, question_text, question_type, min_val, max_val)
        answers[question_id] = answer
        st.divider()
    
    # Submit buttons
    col1, col2 = st.columns([0.5, 0.5])
    
    with col1:
        if st.button("✓ Submit Form", type="primary", use_container_width=True):
            try:
                form.submit_response(answers, user_name)
                st.success("Form submitted successfully!")
                st.balloons()
                
                # Clear session state
                for key in list(st.session_state.keys()):
                    if key.startswith("answer_"):
                        del st.session_state[key]
                
                # Go back to list
                st.session_state[view_key] = "list"
                st.session_state[form_id_key] = None
                st.rerun()
            except Exception as e:
                st.error(f"Error submitting form: {str(e)}")
    
    with col2:
        if st.button("✕ Cancel", use_container_width=True):
            st.session_state[view_key] = "list"
            st.session_state[form_id_key] = None
            st.rerun()
