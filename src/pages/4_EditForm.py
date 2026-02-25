import streamlit as st
from database_manager import (
    create_form, get_form_by_id, update_form, get_questions_by_form,
    add_question, update_question, delete_question, reorder_questions, check_permission
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

# Determine if we're creating a new form or editing an existing one
form_id = None
is_new_form = False

# Initialize session state for form editing
if "current_form_id" not in st.session_state:
    st.session_state.current_form_id = None
if "is_creating_form" not in st.session_state:
    st.session_state.is_creating_form = False

# Check for navigation from Forms page
if "edit_form_id" in st.session_state:
    st.session_state.current_form_id = st.session_state.edit_form_id
    del st.session_state.edit_form_id
elif "new_form" in st.session_state:
    st.session_state.is_creating_form = True
    del st.session_state.new_form

form_id = st.session_state.current_form_id
is_new_form = st.session_state.is_creating_form

# Back button
if st.button("← Back to Forms"):
    st.session_state.current_form_id = None
    st.session_state.is_creating_form = False
    st.switch_page("pages/3_Forms.py")

st.divider()

# Form Details Section
if is_new_form:
    st.title("Create New Form")
    
    col1, col2 = st.columns(2)
    with col1:
        form_name = st.text_input("Form Name", placeholder="e.g., Employee Satisfaction Survey")
    with col2:
        form_description = st.text_area("Description", placeholder="Brief description of the form", height=100)
    
    if st.button("Create Form", type="primary"):
        if form_name.strip():
            new_form_id = create_form(form_name, form_description, st.session_state.user.first_name + " " + st.session_state.user.last_name)
            st.session_state.current_form_id = new_form_id
            st.session_state.is_creating_form = False
            st.rerun()
        else:
            st.error("Form name cannot be empty")
else:
    if form_id:
        form = get_form_by_id(form_id)
        if form:
            st.title(form[1])  # form[1] is the name
            
            col1, col2 = st.columns(2)
            with col1:
                form_name = st.text_input("Form Name", value=form[1])
            with col2:
                form_description = st.text_area("Description", value=form[2] or "", height=100)
            
            if st.button("Save Form Details", type="primary"):
                update_form(form_id, form_name, form_description)
                st.success("Form details updated!")
        else:
            st.error("Form not found")
            st.stop()
    else:
        st.error("No form selected")
        st.stop()

# Questions Section
st.divider()
st.subheader("Form Questions")

if form_id:
    # Add new question section at the top
    st.markdown("Add New Question")
    col1, col2, col3 = st.columns([0.5, 0.25, 0.25])
    
    with col1:
        new_question_text = st.text_input("Question Text", placeholder="e.g., How satisfied are you?", key="new_question_text")
    
    with col2:
        new_question_type = st.selectbox(
            "Question Type",
            ["Text Box", "0-5 Rating", "1-10 Rating", "Multiple Choice"],
            key="new_question_type"
        )
    
    with col3:
        if st.button("Add Question", use_container_width=True, type="primary"):
            if new_question_text.strip():
                # Determine min/max values based on type
                if new_question_type == "0-5 Rating":
                    min_v, max_v = 0, 5
                elif new_question_type == "1-10 Rating":
                    min_v, max_v = 1, 10
                else:
                    min_v, max_v = None, None
                
                add_question(form_id, new_question_text, new_question_type, min_v, max_v)
                st.success("Question added!")
                st.rerun()
            else:
                st.error("Question text cannot be empty")
    
    st.divider()
    
    questions = get_questions_by_form(form_id)
    
    # Display existing questions
    if questions:
        st.markdown("#### Existing Questions")
        
        for idx, question in enumerate(questions):
            question_id, question_text, question_type, min_val, max_val, order = question
            
            with st.expander(f"Question {idx + 1}: {question_text[:50]}{'...' if len(question_text) > 50 else ''}", expanded=False):
                col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
                
                with col1:
                    new_text = st.text_input("Question Text", value=question_text, key=f"text_{question_id}")
                    new_type = st.selectbox(
                        "Question Type",
                        ["Text Box", "0-5 Rating", "1-10 Rating", "Multiple Choice"],
                        index=["Text Box", "0-5 Rating", "1-10 Rating", "Multiple Choice"].index(question_type) if question_type in ["Text Box", "0-5 Rating", "1-10 Rating", "Multiple Choice"] else 0,
                        key=f"type_{question_id}"
                    )
                
                with col2:
                    if new_type in ["0-5 Rating", "1-10 Rating"]:
                        st.info(f"Min: {min_val}, Max: {max_val}")
                    st.empty()
                
                with col3:
                    if st.button("Delete", key=f"del_{question_id}", use_container_width=True):
                        delete_question(question_id)
                        st.rerun()
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Update Question", key=f"upd_{question_id}"):
                        # Determine min/max values based on type
                        if new_type == "0-5 Rating":
                            min_v, max_v = 0, 5
                        elif new_type == "1-10 Rating":
                            min_v, max_v = 1, 10
                        else:
                            min_v, max_v = None, None
                        
                        update_question(question_id, new_text, new_type, min_v, max_v)
                        st.success("Question updated!")
                        st.rerun()
    else:
        st.info("No questions added yet.")
