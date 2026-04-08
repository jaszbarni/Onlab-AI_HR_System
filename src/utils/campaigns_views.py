"""Views for campaign and form management."""
import random
import streamlit as st
from database_manager import (
    add_form_assignments, check_permission, create_form, get_all_employees, update_assignment_status, update_form, create_campaign, get_all_campaigns, get_campaign_by_id, get_forms_by_campaign,
    update_campaign, delete_campaign, update_campaign_status,
    add_question, update_question, delete_question, get_all_form_templates, delete_form, create_form_from_template,
    get_assignments_by_form
)
from classes.form_template_class import FormTemplate
from utils.common import get_user_name, back_button, delete_confirmation_dialog, set_state
import pandas as pd
import altair as alt


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


def show_campaigns_list():
    """Display list of all campaigns."""

    
    if st.button(label="Generate Test campaign", use_container_width=True, disabled=not check_permission("create")):
        with st.spinner("Generating test campaign..."):
            generate_test_campaign()
        st.rerun()

    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.header("Campaigns", text_alignment="left")
    with col2:
        if st.button(label="Create Campaign", use_container_width=True, type="primary", disabled=not check_permission("create")):
            set_state(campaigns_view="create_campaign")

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
                        set_state(campaigns_view="campaign_forms", current_campaign_id=campaign_id)
                
                with col3:
                    if st.button("Edit", key=f"edit_campaign_{campaign_id}", use_container_width=True, disabled=not check_permission("update")):
                        set_state(campaigns_view="edit_campaign", current_campaign_id=campaign_id)
                
                with col4:
                    if st.button("Delete", key=f"delete_campaign_{campaign_id}", use_container_width=True, disabled=not check_permission("delete")):
                        delete_confirmation_dialog("campaign", delete_campaign, campaign_id)


def show_create_campaign():
    """Create a new campaign."""
    
    # Back button
    if st.button("← Back to Campaigns"):
        set_state(campaigns_view="list")

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
            set_state(campaigns_view="campaign_forms", current_campaign_id=campaign_id)
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
        set_state(campaigns_view="list", current_campaign_id=None)
    

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
            set_state(campaigns_view="campaign_forms")
    with col2:
        if st.button("Edit forms", use_container_width=True, disabled=is_closed):
            set_state(campaigns_view="campaign_forms")


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
        set_state(campaigns_view="list", current_campaign_id=None)
    
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title(f"Campaign: {campaign_name}")
        if campaign_description:
            st.caption(campaign_description)
    with col2:
        if status == "closed":
            if st.button("Reopen campaign", use_container_width=True, type="primary", disabled=not check_permission("delete")):
                update_campaign_status(campaign_id, "open")
                st.success("Campaign reopened!")
                st.rerun()
        else:
            if st.button("Close campaign", use_container_width=True, type="primary", disabled=not check_permission("delete")):
                update_campaign_status(campaign_id, "closed")
                st.success("Campaign closed!")
                st.rerun()


    
    st.divider()
    
    # Campaign actions
    col1, col2, col3, col4, col5 = st.columns(5, gap="small")
    with col1:
        if st.button(label="Edit this campaign", use_container_width=True, disabled=(status == "closed") | (not check_permission("update"))):
            set_state(campaigns_view="edit_campaign")
    with col2:
        if st.button(label="Show statistics", use_container_width=True):
            set_state(campaigns_view="statistics")
    with col3:
        if st.button("Create new form", key="create_form", use_container_width=True, disabled=(status == "closed") | (not check_permission("create"))):
            set_state(campaigns_view="edit_form", current_form_id=None)
    with col4:
        if st.button("Add templates", key="add_templates", use_container_width=True, disabled=(status == "closed") | (not check_permission("update"))):
            add_template_dialog(campaign_id)
    with col5:
        if st.button("Assign employees", key=f"assign_{campaign_id}", use_container_width=True, disabled=(status == "closed") | (not check_permission("create")), type="primary"):
            set_state(campaigns_view="assign_group")
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

                with col2:
                    assignments = get_assignments_by_form(form_id)
                    if assignments:
                        with st.expander(f"Assignments ({len(assignments)})"):
                            for assignment in assignments:
                                a_id, filler_name, target_name, a_status = assignment
                                status_emoji = "✅" if a_status == "completed" else "⏳"
                                st.caption(f"{filler_name} ➡️ {target_name} {status_emoji}")
                    else:
                        st.caption("No assignments")
                
                with col3:
                    if st.button("Edit", key=f"edit_{form_id}", use_container_width=True, disabled=(status == "closed") | (not check_permission("update"))):
                        set_state(campaigns_view="edit_form", current_form_id=form_id)
                
                with col4:
                    if st.button("Delete", key=f"delete_{form_id}", use_container_width=True, disabled=(status == "closed") | (not check_permission("delete"))):
                        delete_confirmation_dialog("form", delete_form, form_id)
                

def show_edit_form(campaign_id):
    """Edit a form within a campaign."""
    form_id = st.session_state.current_form_id
    is_new_form = form_id is None

    # Back button
    if st.button("← Back to forms"):
        set_state(campaigns_view="campaign_forms", current_form_id=None)
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
                st.success("Form created!")
                set_state(current_form_id=new_form_id)
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
                st.success("Form created!")
                set_state(**{form_id_key: new_form_id})
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
        col1, col2, col3 = st.columns([0.4, 0.4, 0.2])
        
        with col1:
            new_question_text = st.text_input("Question Title", placeholder="e.g., How satisfied are you?", key="new_question_text")
            new_question_desc = st.text_area("Question Description", placeholder="Additional details...", key="new_question_desc")
        
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

def show_statistics():
    """Display statistics for a campaign."""
    
    if st.button("← Back to forms"):
        set_state(campaigns_view="campaign_forms")

    st.title("Statistics")

    st.divider()
    
    campaign_id = st.session_state.get("current_campaign_id")
    if not campaign_id:
        st.error("No campaign selected.")
        return

    forms = get_forms_by_campaign(campaign_id)
    if not forms:
        st.info("No forms available for this campaign.")
        return

    data = []
    for form in forms:
        form_id = form[0]
        assignments = get_assignments_by_form(form_id)
        
        form_template = FormTemplate(form_id)
        responses = form_template.get_responses()
        
        for response in responses:
            resp_id = response[0]
            submitted_by = response[1]
            
            # Find target employee for this submission
            target_name = "Unknown"
            for a in assignments:
                if a[1] == submitted_by:
                    target_name = a[2]
                    break
            
            answers = form_template.get_response_details(resp_id)
            for ans in answers:
                # ans = (question_id, question_text, question_type, answer)
                q_text = ans[1]
                q_type = ans[2]
                val = ans[3]
                
                if q_type in ["0-5 Rating", "1-10 Rating"]:
                    try:
                        score = float(val)
                        data.append({
                            "Employee": target_name,
                            "Question": q_text,
                            "Score": score
                        })
                    except ValueError:
                        pass
    
    if data:
        df = pd.DataFrame(data)
        
        # Group by Question to calculate the summarized mean score
        df_summary = df.groupby("Question")["Score"].mean().reset_index()
        
        st.subheader("Summarized Evaluations")
        chart = alt.Chart(df_summary).mark_bar().encode(
            x=alt.X('Score:Q', title='Mean Score').scale(domain=(0, 5)),
            y=alt.Y('Question:N', title='', axis=alt.Axis(labelLimit=0)),
            color=alt.Color('Question:N', legend=None)
        )
        st.altair_chart(chart, use_container_width=True)
        
        st.divider()
        
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Summarized Statistics")
            df_summary.set_index("Question", inplace=True)
            st.dataframe(df_summary, use_container_width=True)
        with col2:
            st.subheader("Score Distribution")
            point_chart = alt.Chart(df).mark_circle(size=300).encode(
                x=alt.X('Score:Q', title='Score').scale(domain=(0, 5)),
                y=alt.Y('Question:N', title='', axis=alt.Axis(labelLimit=0)),
                opacity=alt.value(0.3),
                color=alt.value('Yellow')
            )
            st.altair_chart(point_chart, use_container_width=True)
    else:
        st.info("No rating evaluations have been submitted yet.")


def show_list_view(view_key, form_id_key):
    """Display list of available forms."""
    # Preload forms for roles if they don't exist

    col1, col2 = st.columns([0.8, 0.2])
    with col1:
            st.subheader("Campaigns", text_alignment="left")
    with col2:
        if st.button(label="Add new form", use_container_width=True):
            set_state(**{view_key: "edit", form_id_key: None})

    st.divider()

    forms = get_all_form_templates

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
                        set_state(**{view_key: "edit", form_id_key: form_id})
                
                with col3:
                    if st.button("Delete", key=f"delete_{form_id}", use_container_width=True):
                        delete_confirmation_dialog("form", delete_form, form_id)


#----------------------------- TEST CAMPAIGN ----------------------------------------

def generate_test_campaign():
    """Generate a test template with predefined questions, campaign, and responses."""
    employees = get_all_employees()
    user_name = get_user_name()
    
    if not employees:
        st.warning("Nincs munkatárs a rendszerben. Kérlek, először generálj teszt felhasználókat.")
        return

    template_name = "Vezetői Teljesítményértékelő Sablon"
    template_description = "Automatikusan generált teszt sablon vezetői kompetenciák értékelésére."
    
    template_id = create_form(template_name, template_description, user_name, is_template=False)
    
    q1_title = "Stratégiai szemlélet, üzleti gondolkodás"
    q1_desc = """
    Érti, mitől lehet sikeres a cég és a saját divíziója,
    Felismeri az üzleti lehetőségeket, kockázatokat,
    Képes a stratégiai célokat konkrét, megvalósítható lépésekre bontani,
    Összehangolja a saját területét a szervezeti célokkal.

    Véleményem szerint kollégám ezen a területen nyújtott teljesítménye:
    """
    add_question(template_id, q1_title, q1_desc, "0-5 Rating", 0, 5)
    
    q2_title = "Az értékelés rövid indoklása (erősségek, gyengeségek)"
    add_question(template_id, q2_title, None, "Text Box", None, None)

    q3_title = "Változáskezelés és innováció"
    q3_desc = """
    Nyitott az új ötletekre, fejlesztési javaslatokra,
    Képes a változások bevezetését tervezetten és kommunikáltan végig vinni,
    Innovatív,
    Részt vesz az új eljárások, rendszerek bevezetésében.

    Véleményem szerint kollégám ezen a területen nyújtott teljesítménye:
    """
    add_question(template_id, q3_title, q3_desc, "0-5 Rating", 0, 5)
    
    q4_title = "Az értékelés rövid indoklása (erősségek, gyengeségek)"
    add_question(template_id, q4_title, None, "Text Box", None, None)

    q5_title = "Csapatirányítás és motiváció"
    q5_desc = """
    Felismeri és fejleszti a munkatársak képességeit,
    Megfelelően motiválja a csapat tagjait,
    Támogató és konstruktív munkahelyi légkört teremt,
    Képes kezelni a csapaton belüli konfliktusokat.

    Véleményem szerint kollégám ezen a területen nyújtott teljesítménye:
    """
    add_question(template_id, q5_title, q5_desc, "0-5 Rating", 0, 5)
    
    q6_title = "Az értékelés rövid indoklása (erősségek, gyengeségek)"
    add_question(template_id, q6_title, None, "Text Box", None, None)

    q7_title = "Döntéshozatal és problémamegoldás"
    q7_desc = """
    Időben és határozottan hoz meg nehéz döntéseket is,
    A döntések meghozatala előtt megfelelően tájékozódik,
    Proaktív a felmerülő problémák azonosításában és kezelésében,
    Vállalja a felelősséget a meghozott döntésekért.

    Véleményem szerint kollégám ezen a területen nyújtott teljesítménye:
    """
    add_question(template_id, q7_title, q7_desc, "0-5 Rating", 0, 5)
    
    q8_title = "Az értékelés rövid indoklása (erősségek, gyengeségek)"
    add_question(template_id, q8_title, None, "Text Box", None, None)

    q9_title = "Kommunikáció és visszajelzés"
    q9_desc = """
    Világosan és egyértelműen fogalmazza meg az elvárásokat,
    Rendszeres és építő jellegű visszajelzést ad a munkatársaknak,
    Értő figyelemmel hallgatja meg mások véleményét,
    Hatékonyan kommunikál a társosztályokkal és a vezetőséggel.

    Véleményem szerint kollégám ezen a területen nyújtott teljesítménye:
    """
    add_question(template_id, q9_title, q9_desc, "0-5 Rating", 0, 5)
    
    q10_title = "Az értékelés rövid indoklása (erősségek, gyengeségek)"
    add_question(template_id, q10_title, None, "Text Box", None, None)

    q11_title = "Eredményorientáltság és felelősségvállalás"
    q11_desc = """
    Fókuszban tartja a kitűzött célok elérését,
    Következetes a minőségi munkavégzés megkövetelésében,
    Felelősséget vállal a saját és a csapata munkájáért,
    Példamutatással jár elöl a mindennapi feladatokban.

    Véleményem szerint kollégám ezen a területen nyújtott teljesítménye:
    """
    add_question(template_id, q11_title, q11_desc, "0-5 Rating", 0, 5)
    
    q12_title = " Az értékelés rövid indoklása (erősségek, gyengeségek)"
    add_question(template_id, q12_title, None, "Text Box", None, None)
    
    # Create a second template for Peer evaluation
    template2_name = "Munkatársi Teljesítményértékelő Sablon"
    template2_description = "Automatikusan generált teszt sablon munkatársi kompetenciák értékelésére."
    template2_id = create_form(template2_name, template2_description, user_name, is_template=False)
    
    q1_t2_title = "Csapatmunka és együttműködés"
    q1_t2_desc = "Aktívan részt vesz a közös feladatokban, segíti és támogatja a kollégákat."
    add_question(template2_id, q1_t2_title, q1_t2_desc, "0-5 Rating", 0, 5)
    
    q2_t2_title = "Az értékelés rövid indoklása (erősségek, gyengeségek)"
    add_question(template2_id, q2_t2_title, None, "Text Box", None, None)
    
    q3_t2_title = "Megbízhatóság és precizitás"
    q3_t2_desc = "Határidőre és a megfelelő minőségben végzi el a rábízott feladatokat."
    add_question(template2_id, q3_t2_title, q3_t2_desc, "0-5 Rating", 0, 5)
    
    q4_t2_title = "Az értékelés rövid indoklása (erősségek, gyengeségek)"
    add_question(template2_id, q4_t2_title, None, "Text Box", None, None)
    
    # Create a Campaign and instantiate a Form from the Template
    campaign_id = create_campaign("Példa Kampány Mindenkinek", "Teszt kampány az AI értékeléshez - Teljes szervezet", user_name)
    form_id = create_form_from_template(template_id, campaign_id, user_name)
    form2_id = create_form_from_template(template2_id, campaign_id, user_name)
    
    form1_obj = FormTemplate(form_id)
    form1_qs = form1_obj.get_questions()
    
    form2_obj = FormTemplate(form2_id)
    form2_qs = form2_obj.get_questions()

    send_form = []
    responses_to_submit = []
    n = len(employees)

    def get_emp_name(idx):
        emp = employees[idx % n]
        return f"{emp['first_name']} {emp['last_name']}"

    good_texts = [
        "Kiváló munkát végez, stratégiai látásmódja és problémamegoldó képessége kiemelkedő. Példamutató kolléga.",
        "Mindig megbízható és precíz. A csapat egyik legértékesebb tagja, aki proaktívan áll a kihívásokhoz.",
        "Inspiráló személyiség, aki képes a legnehezebb helyzetekben is motiválni a környezetét. Kiváló eredményeket hoz.",
        "Nagyon jó szakember, a projektjeit mindig időre és magas minőségben szállítja.",
        "Rendkívül együttműködő, a kommunikációja tiszta és érthető. Öröm vele együtt dolgozni."
    ]
    
    bad_texts = [
        "Sajnos a határidőket ritkán tartja be, a kommunikációja pedig sokszor elmarad az elvárttól. A csapatmunkához való hozzáállása javítandó.",
        "Gyakran pontatlan a munkája, és a kritikát nehezen fogadja. Fejlődnie kell a feladatok priorizálásában.",
        "A csapaton belüli konfliktusok gyakran vezethetők vissza a nem megfelelő kommunikációjára. Motiválatlan benyomást kelt.",
        "Többször előfordult, hogy a rábízott feladatokat nem fejezte be időre, ami a többiek munkáját is hátráltatta.",
        "Nem mutat kellő önállóságot, mindig külső iránymutatásra vár a legegyszerűbb feladatoknál is."
    ]
    
    neutral_texts = [
        "Általában megbízható, de időnként előfordulnak apróbb hibák a munkájában. Összességében jó vele együtt dolgozni.",
        "A kötelező feladatokat elvégzi, de ritkán mutat proaktivitást vagy hoz új ötleteket a csapatba.",
        "Alapvetően rendben van a teljesítménye, de a stresszesebb időszakokban hajlamos a kapkodásra.",
        "Megfelelően végzi a munkáját, bár a kommunikációja lehetne egy kicsit nyitottabb és proaktívabb.",
        "Stabil közepes teljesítményt nyújt. Vannak jobb és rosszabb napjai, de alapvetően beilleszkedik a csapatba."
    ]

    for i in range(n):
        target_name = get_emp_name(i)
        
        evaluator1 = get_emp_name(i + 1)
        evaluator2 = get_emp_name(i + 2) if n > 2 else get_emp_name(i)
        evaluator3 = get_emp_name(i + 3) if n > 3 else get_emp_name(i + 1)

        # 1. Good Review
        send_form.append({
            "form_filler": evaluator1,
            "target": target_name,
            "form_type": "Leader",
            "form_id": form_id
        })
        ans_good = {}
        for q in form1_qs:
            q_id, _, q_type = q[0], q[1], q[3]
            if q_type == "0-5 Rating":
                ans_good[q_id] = random.randint(4, 5)
            elif q_type == "Text Box":
                ans_good[q_id] = good_texts[(q_id + i) % len(good_texts)]
        responses_to_submit.append((form1_obj, ans_good, evaluator1))

        # 2. Bad Review
        send_form.append({
            "form_filler": evaluator2,
            "target": target_name,
            "form_type": "Peer",
            "form_id": form2_id
        })
        ans_bad = {}
        for q in form2_qs:
            q_id, _, q_type = q[0], q[1], q[3]
            if q_type == "0-5 Rating":
                ans_bad[q_id] = random.randint(1, 2)
            elif q_type == "Text Box":
                ans_bad[q_id] = bad_texts[(q_id + i) % len(bad_texts)]
        responses_to_submit.append((form2_obj, ans_bad, evaluator2))

        # 3. Neutral Review (Only if enough employees)
        if n > 3:
            send_form.append({
                "form_filler": evaluator3,
                "target": target_name,
                "form_type": "Peer",
                "form_id": form2_id
            })
            ans_neutral = {}
            for q in form2_qs:
                q_id, _, q_type = q[0], q[1], q[3]
                if q_type == "0-5 Rating":
                    ans_neutral[q_id] = random.randint(3, 4)
                elif q_type == "Text Box":
                    ans_neutral[q_id] = neutral_texts[(q_id + i) % len(neutral_texts)]
            responses_to_submit.append((form2_obj, ans_neutral, evaluator3))

    add_form_assignments(send_form)
    
    for f_obj, ans, f_name in responses_to_submit:
        f_obj.submit_response(ans, f_name)

    for f_id in [form_id, form2_id]:
        assigns = get_assignments_by_form(f_id)
        if assigns:
            for assign in assigns:
                update_assignment_status(assign[0], 'completed')
