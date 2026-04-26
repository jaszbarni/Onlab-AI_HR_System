"""Views for form template management."""
import streamlit as st

from classes.form_template_class import FormTemplate
from utils.Form_templates.AI_form_maker import use_AI_questions
from utils.common import get_user_name, delete_confirmation_dialog, set_state
from Database.forms import delete_question, update_question, get_all_form_templates, delete_form, create_form, add_question, update_form
from Database.database_manager import check_permission
from Database.form_response import get_company_values, save_company_values


def render_question_editor(question_id, question_text, question_description, question_type, min_val, max_val, form_id, is_closed=False):
    """Render editor for a question.
    
    Returns:
        bool: True if question was updated
    """
    with st.expander(f"Question: {question_text[:50]}{'...' if len(question_text) > 50 else ''}", expanded=False):
        col1, col2, col3 = st.columns([0.4, 0.4, 0.2])
        
        with col1:
            new_text = st.text_input("Question Title", value=question_text, key=f"text_{question_id}", disabled=is_closed)
            new_desc = st.text_area("Question Description", value=question_description or "", key=f"desc_{question_id}", disabled=is_closed)
        with col2:
            new_type = st.selectbox(
                "Question Type",
                ["Text Box", "0-5 Rating", "1-10 Rating"],
                index=["Text Box", "0-5 Rating", "1-10 Rating"].index(question_type) if question_type in ["Text Box", "0-5 Rating", "1-10 Rating"] else 0,
                key=f"type_{question_id}",
                disabled=is_closed
            )
        
        with col3:
            if st.button("Delete", key=f"del_{question_id}", use_container_width=True, disabled=is_closed):
                delete_confirmation_dialog("question", delete_question, question_id)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update Question", key=f"upd_{question_id}", disabled=is_closed):
                # Determine min/max values based on type
                if new_type == "0-5 Rating":
                    min_v, max_v = 0, 5
                elif new_type == "1-10 Rating":
                    min_v, max_v = 1, 10
                else:
                    min_v, max_v = None, None
                
                update_question(question_id, new_text, new_desc, new_type, min_v, max_v)
                st.success("Question updated!")
                st.rerun()
                return True
    return False

def show_templates_list():
    """Display list of all form templates."""
    col1, col2 = st.columns([0.6, 0.2])
    with col1:
        st.header("Form Templates", text_alignment="left")
    with col2:
        if st.button(label="Create Template", use_container_width=True, type="primary", disabled=not check_permission("create")):
            set_state(forms_view="edit_template", current_form_id=None)
        elif st.button("Add company values for the AI", disabled=not check_permission("create")):
            company_values_dialog()

    st.divider()

    templates = get_all_form_templates()

    if not templates:
        st.info("No form templates created yet. Click 'Create Template' to create one.")
    else:
        st.subheader(f"Existing Templates ({len(templates)})")
        
        for template in templates:
            template_id, name, description = template[:3]
            
            with st.container(border=True):
                col1, col2, col3 = st.columns([0.7, 0.15, 0.15])
                
                with col1:
                    st.markdown(f"### {name}")
                    if description:
                        st.caption(description)
                
                with col2:
                    if st.button("Edit", key=f"edit_{template_id}", use_container_width=True, disabled=not check_permission("update")):
                        set_state(forms_view="edit_template", current_form_id=template_id)
                
                with col3:
                    if st.button("Delete", key=f"delete_{template_id}", use_container_width=True, disabled=not check_permission("delete")):
                        delete_confirmation_dialog("template", delete_form, template_id)

def show_edit_template():
    """Edit a form template."""
    form_id = st.session_state.current_form_id
    is_new_form = form_id is None

    # Back button
    if st.button("← Back to Templates"):
        set_state(forms_view="list", current_form_id=None)
    st.divider()

    # Form Details Section
    if is_new_form:
        st.title("Create New Template")
        
        col1, col2 = st.columns(2)
        with col1:
            form_name = st.text_input("Template Name", placeholder="e.g., Employee Satisfaction Survey")
        with col2:
            form_description = st.text_area("Description", placeholder="Brief description of the template", height=100)
        
        if st.button("Create Template", type="primary"):
            if form_name.strip():
                new_form_id = create_form(form_name, form_description, get_user_name(), is_template=True)
                st.success("Template created!")
                set_state(current_form_id=new_form_id)
            else:
                st.error("Template name cannot be empty")
    else:
        if form_id:
            # Load and edit existing form
            form = FormTemplate(form_id)
            form_info = form.get_form_info()
            
            if form_info:
                st.title(form.get_name())
                
                col1, col2 = st.columns(2)
                with col1:
                    form_name = st.text_input("Template Name", value=form.get_name())
                with col2:
                    form_description = st.text_area("Description", value=form.get_description() or "", height=100)
                

            else:
                st.error("Template not found")
                st.stop()
        else:
            st.error("No template selected")
            st.stop()

    st.divider()

    # Questions Section (only for existing forms)
    if form_id:
        form = FormTemplate(form_id)
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            st.subheader("Template Questions")
        with col2:
            if st.button("Use AI questions", type="secondary", disabled=not check_permission("create"), use_container_width=True):
                AI_question_dialog(form_id, form_name, form_description)


        # Add new question section
        st.markdown("##### Add New Question")
        col1, col2, col3 = st.columns([0.4, 0.4, 0.2])
        
        with col1:
            new_question_text = st.text_input("Question Title", placeholder="e.g., How satisfied are you?", key="new_question_text", label_visibility="collapsed")
            new_question_desc = st.text_area("Question Description", placeholder="Additional details...", key="new_question_desc", label_visibility="collapsed")
        
        with col2:
            new_question_type = st.selectbox(
                "Question Type",
                ["Text Box", "0-5 Rating", "1-10 Rating"],
                key="new_question_type",
                label_visibility="collapsed"
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
                    
                    add_question(form_id, new_question_text, new_question_desc, new_question_type, min_v, max_v)
                    st.success("Question added!")
                    st.rerun()
                else:
                    st.error("Question text cannot be empty")
        
        st.divider()
        
        questions = form.get_questions()
        
        # Display existing questions
        if questions:
            st.markdown("#### Existing Questions")
            
            for idx, question in enumerate(questions):
                question_id, question_text, question_description, question_type, min_val, max_val, order = question
                render_question_editor(question_id, question_text, question_description, question_type, min_val, max_val, form_id)
        else:
            st.info("No questions added yet.")

        if st.button("Save Template Details", type="primary"):  
            update_form(form_id, form_name, form_description)
            st.success("Template details updated!")

@st.dialog("Add Company Values")
def company_values_dialog():
    """Dialog to add company values for the AI."""
    current_value = get_company_values()
    
    updated_value = st.text_area("Values", value=current_value, label_visibility="collapsed")
    
    if st.button("Save", type="primary"):
        save_company_values(updated_value)
        st.success("Values saved!")
        st.rerun()

@st.dialog("How many AI questions")
def AI_question_dialog(form_id, form_name, form_desc):
    num = st.number_input("How many questions?", step=1, min_value=1)
    if st.button("Generate"):
        use_AI_questions(form_id, form_name, form_desc, num)