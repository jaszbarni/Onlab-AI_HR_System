"""Views for campaign and form management."""
import streamlit as st
from database_manager import (
    create_form, update_form, create_campaign, get_all_campaigns, get_campaign_by_id, get_forms_by_campaign,
    update_campaign, delete_campaign, update_campaign_status,
    add_question, update_question, delete_question, get_all_form_templates, delete_form, create_form_from_template
)
from classes.form_template_class import FormTemplate
from utils.common import get_user_name, back_button, delete_confirmation_dialog
from classes.campaign_class import Campaign



def render_question_editor(question_id, question_text, question_type, min_val, max_val, form_id, is_closed=False):
    """Render editor for a question.
    
    Returns:
        bool: True if question was updated
    """
    with st.expander(f"Question: {question_text[:50]}{'...' if len(question_text) > 50 else ''}", expanded=False):
        col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
        
        with col1:
            new_text = st.text_input("Question Text", value=question_text, key=f"text_{question_id}", disabled=is_closed)
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
                
                update_question(question_id, new_text, new_type, min_v, max_v)
                st.success("Question updated!")
                st.rerun()
                return True
    return False


def show_campaigns_list():
    """Display list of all campaigns."""
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.header("Campaigns", text_alignment="left")
    with col2:
        if st.button(label="Create Campaign", use_container_width=True, type="primary"):
            st.session_state.campaigns_view = "create_campaign"
            st.rerun()

    st.divider()

    campaigns = get_all_campaigns()

    if not campaigns:
        st.info("No campaigns created yet. Click 'Create Campaign' to create one.")
    else:
        st.subheader(f"Existing Campaigns ({len(campaigns)})")
        
        for campaign in campaigns:
            campaign_id, name, description, status = campaign
            
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([0.6, 0.15, 0.15, 0.1])
                
                with col1:
                    st.markdown(f"### {name}")
                    if description:
                        st.caption(description)
                    st.markdown(f"**Status:** {status.capitalize()}")
                
                with col2:
                    if st.button("View", key=f"view_{campaign_id}", use_container_width=True):
                        st.session_state.campaigns_view = "campaign_forms"
                        st.session_state.current_campaign_id = campaign_id
                        st.rerun()
                
                with col3:
                    if st.button("Edit", key=f"edit_campaign_{campaign_id}", use_container_width=True):
                        st.session_state.campaigns_view = "edit_campaign"
                        st.session_state.current_campaign_id = campaign_id
                        st.rerun()
                
                with col4:
                    if st.button("Delete", key=f"delete_campaign_{campaign_id}", use_container_width=True):
                        delete_confirmation_dialog("campaign", delete_campaign, campaign_id)


def show_create_campaign():
    """Create a new campaign."""
    
    # Back button
    if st.button("← Back to Campaigns"):
        st.session_state.campaigns_view = "list"
        st.rerun()

    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("Create New Campaign")
    with col2:
        if st.button("Form templates", use_container_width=True):
            st.switch_page("pages/3_Form_Templates.py")

    st.divider()
    
    user_name = get_user_name()
    
    col1, col2 = st.columns(2)
    with col1:
        campaign_name = st.text_input("Campaign Name", placeholder="e.g., Q1 Employee Survey")
    with col2:
        campaign_description = st.text_area("Description", placeholder="Brief description of the campaign", height=100)
    
    st.subheader("Select Form Templates")
    
    templates = get_all_form_templates()
    selected_templates = []

    if not templates:
        st.info("No form templates found. Please create a form template first.")
    else:
        for template in templates:
            template_id, template_name, _ = template[:3]
            if st.checkbox(template_name, key=f"template_{template_id}"):
                selected_templates.append(template_id)

    if st.button("Create Campaign", type="primary"):
        if campaign_name.strip():
            campaign_id = create_campaign(campaign_name, campaign_description, user_name)

            for template_id in selected_templates:
                create_form_from_template(template_id, campaign_id, user_name)

            st.success("Campaign created successfully!")
            st.session_state.campaigns_view = "campaign_forms"
            st.session_state.current_campaign_id = campaign_id
            st.rerun()
        else:
            st.error("Campaign name cannot be empty")




def show_edit_campaign():
    """Edit an existing campaign."""
    campaign_id = st.session_state.current_campaign_id
    campaign = get_campaign_by_id(campaign_id)
    
    if not campaign:
        st.error("Campaign not found")
        st.stop()
    
    campaign_id, name, description, status = campaign
    if st.button("← Back to Campaigns"):
        st.session_state.campaigns_view = "list"
        st.rerun()
    

    st.title(f"Edit Campaign: {name}")
    st.markdown(f"**Status:** {status.capitalize()}")
    
    st.divider()
    
    is_closed = status == 'closed'

    col1, col2 = st.columns(2)
    with col1:
        campaign_name = st.text_input("Campaign Name", value=name, disabled=is_closed)
    with col2:
        campaign_description = st.text_area("Description", value=description or "", height=100, disabled=is_closed)
    
    col1, col2, _ = st.columns([1, 1, 5])
    with col1:
        if st.button("Save Campaign", type="primary", use_container_width=True, disabled=is_closed):
            update_campaign(campaign_id, campaign_name, campaign_description)
            st.success("Campaign updated!")
            st.session_state.campaigns_view = "campaign_forms"
            st.rerun()
    with col2:
        if st.button("Edit forms", use_container_width=True, disabled=is_closed):
            st.session_state.campaigns_view = "campaign_forms"
            st.rerun()


@st.dialog("Add Form Templates")
def add_template_dialog(campaign_id):
    """Dialog to add existing form templates to a campaign."""
    st.write("Select templates to add to this campaign:")
    templates = get_all_form_templates()
    selected_templates = []
    campaign_forms = get_forms_by_campaign(campaign_id)
    campaign_form_names = {f[1] for f in campaign_forms}
    available_templates = [t for t in templates if t[1] not in campaign_form_names] if templates else []

    if not templates:
        st.info("No form templates found. Please create a form template first.")
    elif not available_templates:
        st.info("All available templates are already in this campaign.")
    else:
        for template in available_templates:
            template_id, template_name, _ = template[:3]
            if st.checkbox(template_name, key=f"add_tpl_{template_id}"):
                selected_templates.append(template_id)

    if st.button("Add to Campaign", type="primary", disabled=not available_templates):
        if selected_templates:
            user_name = get_user_name()
            for template_id in selected_templates:
                create_form_from_template(template_id, campaign_id, user_name)
            st.success("Templates added successfully!")
            st.rerun()
        else:
            st.warning("Please select at least one template.")


def show_campaign_forms():
    """Display forms within a campaign."""
    campaign_id = st.session_state.current_campaign_id
    campaign = get_campaign_by_id(campaign_id)
    
    if not campaign:
        st.error("Campaign not found")
        st.stop()
    
    campaign_id, campaign_name, campaign_description, status = campaign
    
    # Header with back button
    if st.button("← Back to campaigns"):
        st.session_state.campaigns_view = "list"
        st.session_state.current_campaign_id = None
        st.rerun()
    
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title(f"Campaign: {campaign_name}")
        if campaign_description:
            st.caption(campaign_description)
    with col2:
        if status == "closed":
            if st.button("Reopen campaign", use_container_width=True, type="primary"):
                update_campaign_status(campaign_id, "open")
                st.success("Campaign reopened!")
                st.rerun()
        else:
            if st.button("Close campaign", use_container_width=True, type="primary"):
                update_campaign_status(campaign_id, "closed")
                st.success("Campaign closed!")
                st.rerun()


    
    st.divider()
    
    # Campaign actions
    col1, col2, col3, col4, col5 = st.columns(5, gap="small")
    with col1:
        if st.button(label="Edit this campaign", use_container_width=True, disabled=status == "closed"):
            st.session_state.campaigns_view = "edit_campaign"
            st.rerun()
    with col2:
        if st.button(label="Show statistics", use_container_width=True):
            st.session_state.campaigns_view = "statistics"
            st.rerun()
    with col3:
        if st.button("Create new form", key="create_form", use_container_width=True, disabled=status == "closed"):
            st.session_state.campaigns_view = "edit_form"
            st.session_state.current_form_id = None
            st.rerun()
    with col4:
        if st.button("Add templates", key="add_templates", use_container_width=True, disabled=status == "closed"):
            add_template_dialog(campaign_id)
    with col5:
        if st.button("Assign employees", key=f"assign_{campaign_id}", use_container_width=True, disabled=status == "closed", type="primary"):
            st.session_state.campaigns_view = "assign_group"
            st.rerun()
    st.divider()
    
    # Display forms in this campaign
    forms = get_forms_by_campaign(campaign_id)

    if not forms:
        st.info("No forms in this campaign yet. Click 'Create Form' to add one.")
    else:
        st.subheader(f"Forms ({len(forms)})")
        
        for form in forms:
            form_id, form_name, form_description = form[:3]
            
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([0.35, 0.25, 0.15, 0.15])
                
                with col1:
                    st.markdown(f"#### {form_name}")
                    if form_description:
                        st.caption(form_description)
                
                with col3:
                    if st.button("Edit", key=f"edit_{form_id}", use_container_width=True, disabled=status == "closed"):
                        st.session_state.campaigns_view = "edit_form"
                        st.session_state.current_form_id = form_id
                        st.rerun()
                
                with col4:
                    if st.button("Delete", key=f"delete_{form_id}", use_container_width=True, disabled=status == "closed"):
                        delete_confirmation_dialog("form", delete_form, form_id)
                

def show_edit_form(campaign_id):
    """Edit a form within a campaign."""
    form_id = st.session_state.current_form_id
    is_new_form = form_id is None

    # Back button
    if st.button("← Back to forms"):
        st.session_state.campaigns_view = "campaign_forms"
        st.session_state.current_form_id = None
        st.rerun()
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
                new_form_id = create_form(form_name, form_description, get_user_name(), campaign_id, is_template=False)
                st.session_state.current_form_id = new_form_id
                st.success("Form created!")
                st.rerun()
            else:
                st.error("Form name cannot be empty")
    else:
        if form_id:
            # Load and edit existing form
            form = FormTemplate(form_id)
            form_info = form.get_form_info()
            
            if form_info:
                st.title(form.get_name())
                
                col1, col2 = st.columns(2)
                with col1:
                    form_name = st.text_input("Form Name", value=form.get_name())
                with col2:
                    form_description = st.text_area("Description", value=form.get_description() or "", height=100)
                

            else:
                st.error("Form not found")
                st.stop()
        else:
            st.error("No form selected")
            st.stop()

    st.divider()

    # Questions Section (only for existing forms)
    if form_id:
        form = FormTemplate(form_id)
        st.subheader("Form Questions")

        # Add new question section
        st.markdown("##### Add New Question")
        col1, col2, col3 = st.columns([0.5, 0.25, 0.25])
        
        with col1:
            new_question_text = st.text_input("Question Text", placeholder="e.g., How satisfied are you?", key="new_question_text", label_visibility="collapsed")
        
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
                    
                    add_question(form_id, new_question_text, new_question_type, min_v, max_v)
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
                question_id, question_text, question_type, min_val, max_val, order = question
                render_question_editor(question_id, question_text, question_type, min_val, max_val, form_id)
        else:
            st.info("No questions added yet.")

        if st.button("Save Form Details", type="primary"):  
            update_form(form_id, form_name, form_description)
            st.success("Form details updated!")


def show_edit_view(view_key, form_id_key):
    """Legacy function for backward compatibility."""
    form_id = st.session_state[form_id_key]
    is_new_form = form_id is None
    user_name = get_user_name()

    # Back button
    back_button(view_key, form_id_key, target_view="list")
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
                new_form_id = create_form(form_name, form_description, user_name)
                st.session_state[form_id_key] = new_form_id
                st.success("Form created!")
                st.rerun()
            else:
                st.error("Form name cannot be empty")
    else:
        if form_id:
            # Load and edit existing form
            form = FormTemplate(form_id)
            form_info = form.get_form_info()
            
            if form_info:
                st.title(form.get_name())
                
                col1, col2 = st.columns(2)
                with col1:
                    form_name = st.text_input("Form Name", value=form.get_name())
                with col2:
                    form_description = st.text_area("Description", value=form.get_description() or "", height=100)
                
                if st.button("Save Form Details", type="primary"):
                    update_form(form_id, form_name, form_description)
                    st.success("Form details updated!")
            else:
                st.error("Form not found")
                st.stop()
        else:
            st.error("No form selected")
            st.stop()

    st.divider()

    # Questions Section (only for existing forms)
    if form_id:
        form = FormTemplate(form_id)
        st.subheader("Form Questions")

        # Add new question section
        st.markdown("Add New Question")
        col1, col2, col3 = st.columns([0.5, 0.25, 0.25])
        
        with col1:
            new_question_text = st.text_input("Question Text", placeholder="e.g., How satisfied are you?", key="new_question_text")
        
        with col2:
            new_question_type = st.selectbox(
                "Question Type",
                ["Text Box", "0-5 Rating", "1-10 Rating"],
                key="new_question_type"
            )
        
        with col3:
            if st.button("Add Question", use_container_width=True, type="secondary"):
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
        
        questions = form.get_questions()
        
        # Display existing questions
        if questions:
            st.markdown("#### Existing Questions")
            
            for idx, question in enumerate(questions):
                question_id, question_text, question_type, min_val, max_val, order = question
                render_question_editor(question_id, question_text, question_type, min_val, max_val, form_id)
        else:
            st.info("No questions added yet.")

def show_statistics():
    """Display statistics for a campaign."""
    
    if st.button("← Back to forms"):
        st.session_state.campaigns_view = "campaign_forms"
        st.rerun()

    st.title("Statistics")

    st.write("Not implemented yet")

    st.divider()
    


def show_list_view(view_key, form_id_key):
    """Display list of available forms."""
    # Preload forms for roles if they don't exist

    col1, col2 = st.columns([0.8, 0.2])
    with col1:
            st.subheader("Campaigns", text_alignment="left")
    with col2:
        if st.button(label="Add new form", use_container_width=True):
            st.session_state[view_key] = "edit"
            st.session_state[form_id_key] = None
            st.rerun()

    st.divider()

    forms = get_all_forms()

    if not forms:
        st.info("No forms created yet. Click 'Add new form' to create one.")
    else:
        st.subheader(f"Existing Forms ({len(forms)})")
        
        for form in forms:
            form_id, name, description = form
            
            with st.container(border=True):
                col1, col2, col3 = st.columns([0.7, 0.15, 0.15])
                
                with col1:
                    st.markdown(f"### {name}")
                    if description:
                        st.caption(description)
                
                with col2:
                    if st.button("Edit", key=f"edit_{form_id}", use_container_width=True):
                        st.session_state[view_key] = "edit"
                        st.session_state[form_id_key] = form_id
                        st.rerun()
                
                with col3:
                    if st.button("Delete", key=f"delete_{form_id}", use_container_width=True):
                        delete_confirmation_dialog("form", delete_form, form_id)
