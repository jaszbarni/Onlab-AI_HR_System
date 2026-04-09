"""Views for form template management."""
import json
import os

import streamlit as st
from database_manager import (
    check_permission, create_form, update_form, get_all_form_templates, delete_form,
    add_question, update_question, delete_question,
    get_company_values, save_company_values
)
from dotenv import load_dotenv, find_dotenv
from classes.form_template_class import FormTemplate
from utils.common import get_user_name, back_button, delete_confirmation_dialog, set_state

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

def use_AI_questions(form_id, form_name, form_desc, num_of_questions):
    comp_values = get_company_values()

    if not comp_values:
        st.error("Company values are not set. Please add them before generating AI questions.")
        return

    form = FormTemplate(form_id)
    existing_qs = form.get_questions()
    if existing_qs:
        existing_questions_text = "\n".join([f"- {q[1]}" for q in existing_qs])
    else:
        existing_questions_text = "None"

    prompt = """
        You are an expert HR assistant tasked with creating insightful evaluation questions.
        Your goal is to generate a set of questions for a form based on its title, description, and the company's core values.

        **Company Values:**
        {comp_values}

        **Form Details:**
        - **Title:** {form_name}
        - **Description:** {form_desc}

        **Existing Questions:**
        {existing_questions}

        **Task:**
        Generate exactly {num_of_questions} NEW questions. Ensure they do not duplicate the existing questions.
        For each question, provide:
        1.  `question_text`: The main title of the question no more than 40 characters.
        2.  `question_description`: A brief, optional description or context for the question.
        3.  `question_type`: The type of question. Choose from "Text Box", "0-5 Rating", or "1-10 Rating". A rating question is preferred for measurable feedback, but use a text box for open-ended questions.

        **Output Format:**
        You MUST output a valid JSON array of objects, with no other text before or after the JSON.
        Example format:
        [
        {{
            "question_text": "Stratégiai szemlélet, üzleti gondolkodás",
            "question_description": "• Érti, mitől lehet sikeres a cég és a saját divíziója.\n
                                    • Felismeri az üzleti lehetőségeket, kockázatokat.\n
                                    • Képes a stratégiai célokat konkrét, megvalósítható lépésekre bontani.\n
                                    • Összehangolja a saját területét a szervezeti célokkal.\n
                                    Véleményem szerint kollégám ezen a területen nyújtott teljesítménye:",
            "question_type": "0-5 Rating"
        }},
        {{
            "question_text": "Az értékelés rövid indoklása (erősségek, gyengeségek)",
            "question_description": "",
            "question_type": "Text Box"
        }}
        ]
        """

    with st.spinner("Generating AI questions..."):
        try: 
            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import StrOutputParser

            #setup AI
            load_dotenv(find_dotenv())

            api_key = os.environ.get("OPENROUTER_API_KEY")
            if not api_key and hasattr(st, "secrets") and "OPENROUTER_API_KEY" in st.secrets:
                api_key = st.secrets["OPENROUTER_API_KEY"]

            if not api_key:
                st.error("API Key is missing! Please set `OPENROUTER_API_KEY` in your `.env` or `.streamlit/secrets.toml` file.")
                return

            llm = ChatOpenAI(
                #model="nvidia/nemotron-3-super-120b-a12b:free",
                model="openai/gpt-oss-20b:free",
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                max_retries=5, # Automatically retry on 429 rate limit errors
            )

            chat_prompt = ChatPromptTemplate.from_messages([("system", prompt)])
            chain = chat_prompt | llm | StrOutputParser()
            response_str = chain.invoke({
                "comp_values": comp_values,
                "form_name": form_name,
                "form_desc": form_desc,
                "num_of_questions": num_of_questions,
                "existing_questions": existing_questions_text
            })

            try:
                start_index = response_str.index('[')
                end_index = response_str.rindex(']') + 1
                json_part = response_str[start_index:end_index]
                questions_to_add = json.loads(json_part)
            except (ValueError, json.JSONDecodeError):
                st.error("Failed to parse AI response as JSON. The response was:")
                st.code(response_str)
                return

            for q in questions_to_add:
                q_text = q.get("question_text")
                q_desc = q.get("question_description")
                q_type = q.get("question_type")

                if not q_text or not q_type:
                    st.warning(f"Skipping invalid question from AI: {q}")
                    continue

                min_v, max_v = None, None
                if q_type == "0-5 Rating":
                    min_v, max_v = 0, 5
                elif q_type == "1-10 Rating":
                    min_v, max_v = 1, 10

                add_question(form_id, q_text, q_desc, q_type, min_v, max_v)

            st.success(f"{len(questions_to_add)} questions generated and added successfully!")
            st.rerun()

        except json.JSONDecodeError:
            st.error("Failed to parse AI response as JSON. The response was:")
            st.code(response_str)
        except Exception as e:
            st.error(f"Failed to generate questions: {e}")