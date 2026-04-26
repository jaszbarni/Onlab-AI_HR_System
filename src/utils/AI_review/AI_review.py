import os
import json
import hashlib
import webbrowser
import streamlit as st
from dotenv import load_dotenv, find_dotenv
from utils.common import set_state
import datetime
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent
import phoenix as px
from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor
from Database.employee import get_all_employees
from Database.database_manager import check_permission
from Database.form_response import get_evaluations_for_employee, get_ai_review, save_ai_review

def employee_list_view():
    with st.spinner("Loading..."):
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
                    if st.button("Get Review", key=f"review_{employee['id']}", use_container_width=True, disabled=not check_permission("create")):
                        set_state(review_view="review", current_employee_id=employee['id'])
        else:
            st.info("No employees found.")

def review_view():

    if st.button("← Back to employee list"):
        set_state(review_view="list", current_employee_id=None)

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

    evals = get_evaluations_for_employee(employee_id)
    eval_date = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S") if evals else "Nincs adat"
    groups_str = ", ".join(employee.get("groups", [])) if employee.get("groups") else "Nincs"
    
    # Check if we already have a generated review that is up to date
    evals_json = json.dumps(evals, ensure_ascii=False, sort_keys=True)
    evals_hash = hashlib.sha256(evals_json.encode('utf-8')).hexdigest()
    
    saved_review = get_ai_review(employee_id)
    
    if saved_review and saved_review[1] == evals_hash:
        eval_date = saved_review[3] if len(saved_review) > 3 and saved_review[3] else eval_date
        st.markdown(
                f"### Név: **{employee['first_name']} {employee['last_name']}**\n" +
                f"### Pozíció: **{employee['position']}** ({employee['position_acquired_date'].split()[0]} óta)\n" + 
                f"### Munkakör(ök): **{groups_str}**\n" + 
                f"### Értékelés dátuma: **{eval_date}**\n\n" + 
                saved_review[0]
            )
        st.info(f"Betöltve a gyorsítótárból")
        
        if not st.button("Regenerate Review"):
            return
        st.divider()
    
    with st.spinner("Generating AI review..."):
        try:
            # Start the local Phoenix app and automatically instrument LangChain
            session = px.launch_app()
            tracer_provider = register(project_name="Onlab", auto_instrument=True)
            LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

            webbrowser.open(session.url)

            #setup AI
            load_dotenv(find_dotenv())

            api_key = os.environ.get("OPENROUTER_API_KEY")
            if not api_key and hasattr(st, "secrets") and "OPENROUTER_API_KEY" in st.secrets:
                api_key = st.secrets["OPENROUTER_API_KEY"]
                
            if not api_key:
                st.error("API Key is missing! Please set `OPENROUTER_API_KEY` in your `.env` or `.streamlit/secrets.toml` file.")
                return

            llm = ChatOpenAI(
                #model="nvidia/nemotron-3-super-120b-a12b:free", #2287 tk, 2m
                #model="z-ai/glm-4.5-air:free", #5041 tk, 2m 25s
                #model="openai/gpt-oss-120b:free", #5500 tk, 34 s
                #model="openai/gpt-oss-20b:free", #350 tk 6s
                model="arcee-ai/trinity-large-preview:free", #5500 tk, 1m 18s 

                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                max_retries=5, # Automatically retry on 429 rate limit errors
            )

            @tool
            def fetch_evaluations(employee_id: int) -> str:
                """Get all evaluations and reviews submitted by other employees for a specific employee."""
                return json.dumps(get_evaluations_for_employee(employee_id), ensure_ascii=False)
            
            @tool
            def get_template() -> str:
                """Get the text template that the AI review should follow."""
                # Construct absolute path relative to this script's location
                template_path = os.path.join(os.path.dirname(__file__), "AI_review_template.md")
                with open(template_path, mode="r", encoding="utf-8") as f:
                    return f.read()

            tools = [fetch_evaluations, get_template]

            agent = create_agent(llm, tools, system_prompt=(
                                "You are an expert HR evaluation assistant. Your sole purpose is to process peer evaluations "
                                "and output a highly structured Markdown report in Hungarian.\n\n"
                                "CRITICAL INSTRUCTIONS:\n"
                                "1. You MUST use the `fetch_evaluations` tool to get the raw data.\n"
                                "2. You MUST use the `get_template` tool to get the strict formatting rules and the exact layout.\n"
                                "3. You MUST completely omit the employee's name from the final output.\n"
                                "4. Output ONLY the filled Markdown template. Do not include conversational filler, greetings, or explanations.\n"
                                "5. If there are no evaluations available, output: 'Nincs elegendő adat az értékeléshez.'"
            ))

            response = agent.invoke(
                {"messages": [{"role": "user", "content": f"Please summarize and evaluate the performance of {employee['first_name']} {employee['last_name']} (Employee ID: {employee_id}) based on their peer evaluations."}]}
            )
            
            review_text = response["messages"][-1].content
            review_date = save_ai_review(employee_id, review_text, evals_hash, eval_date)
            
            st.markdown(
                f"### Név: **{employee['first_name']} {employee['last_name']}**\n" +
                f"### Pozíció: **{employee['position']}**\n" + 
                f"### Munkakör(ök): **{groups_str}**\n" + 
                f"### Értékelés dátuma: **{eval_date}**\n" + 
                "---\n\n" +
                review_text
            )
            st.success(f"Értékelés sikeresen generálva: {review_date}")
                
        except Exception as e:
            st.error(f"Failed to generate review: {e}")
