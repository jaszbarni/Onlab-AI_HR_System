import os
import json
import streamlit as st
from database_manager import get_all_employees, get_evaluations_for_employee
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain.agents import create_agent

def employee_list_view():
    st.title("AI reviews")

    all_employees = get_all_employees()

    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.header("Employee List", text_alignment="left")
        
    st.divider()

    if all_employees:
        col1, col2, col3, col4 = st.columns([1, 3, 3, 2])
        with col1:
            st.caption("**ID**", text_alignment="left")
        with col2:
            st.caption("**Name**", text_alignment="left")
        with col3:
            st.caption("**Email**", text_alignment="left")
        with col4:
            st.caption("**Actions**", text_alignment="center")

        for employee in all_employees:
            col1, col2, col3, col4 = st.columns([1, 3, 3, 2], vertical_alignment="center")
            with col1:
                st.write(f"{employee['id']}")
            with col2:
                st.write(f"**{employee['first_name']} {employee['last_name']}**")
            with col3:
                st.write(employee['email'])
            with col4:
                if st.button("Generate Review", key=f"review_{employee['id']}", use_container_width=True):
                    st.session_state.review_view = "review"
                    st.session_state.current_employee_id = employee['id']
                    st.rerun()
    else:
        st.info("No employees found.")

def review_view():

    if st.button("← Back to employee list"):
        st.session_state.review_view = "list"
        st.session_state.current_employee_id = None
        st.rerun()

    employee_id = st.session_state.current_employee_id
    if not employee_id:
        st.error("No employee selected.")
        return

    # fetch employee details for context
    all_employees = get_all_employees()
    employee = next((e for e in all_employees if e['id'] == employee_id), None)
    if not employee:
        st.error("Employee not found.")
        return

    st.title(f"AI review for {employee['first_name']} {employee['last_name']}")

    #setup AI
    load_dotenv(find_dotenv())

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key and hasattr(st, "secrets") and "OPENROUTER_API_KEY" in st.secrets:
        api_key = st.secrets["OPENROUTER_API_KEY"]
        
    if not api_key:
        st.error("API Key is missing! Please set `OPENROUTER_API_KEY` in your `.env` or `.streamlit/secrets.toml` file.")
        return

    llm = ChatOpenAI(
        model="nvidia/nemotron-3-super-120b-a12b:free",
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )

    @tool
    def fetch_evaluations(employee_id: int) -> str:
        """Get all evaluations and reviews submitted by other employees for a specific employee."""
        return json.dumps(get_evaluations_for_employee(employee_id), ensure_ascii=False)
    
    @tool
    def get_template() -> str:
        """Get the text template that the AI review should follow."""
        # Construct absolute path relative to this script's location
        template_path = os.path.join(os.path.dirname(__file__), "AI_template.txt")
        with open(template_path, mode="r", encoding="utf-8") as f:
            return f.read()

    tools = [fetch_evaluations, get_template]

    agent = create_agent(llm, tools, system_prompt=
                         "You are an HR assistant that helps evaluate employees. " \
                         "Use the provided tools to fetch evaluations and summarize them according to the template. " \
                         "If no evaluations exist, state that clearly." \
                         "Use hungarian as your main language and answer in hungarian" \
                         "You will make the answer in Markdown format")
    
    with st.spinner("Generating AI review..."):
        try:
            response = agent.invoke(
                {"messages": [{"role": "user", "content": f"Please summarize and evaluate the performance of {employee['first_name']} {employee['last_name']} (Employee ID: {employee_id}) based on their peer evaluations."}]}
            )
            
            evals = get_evaluations_for_employee(employee_id)
            eval_date = evals[0]['submitted_date'] if evals else "Nincs adat"
            groups_str = ", ".join(employee.get("groups", [])) if employee.get("groups") else "Nincs"
            
            st.markdown(
                f"### Név: **{employee['first_name']} {employee['last_name']}**\t\tPozíció: **{employee['role']}**\n\n" + 
                f"### Osztály: **{groups_str}**\t\t Értékelés dátuma: **{eval_date}**\n\n" + 
                response["messages"][-1].content
            )
                
        except Exception as e:
            st.error(f"Failed to generate review: {e}")
