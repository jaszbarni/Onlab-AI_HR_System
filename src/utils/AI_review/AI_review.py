import os
import json
import hashlib
import webbrowser
import streamlit as st
from dotenv import load_dotenv, find_dotenv
from Database.db_campaign import get_all_campaigns, get_campaign_by_id
from utils.common import set_state
import datetime
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent
import phoenix as px
from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor
from Database.db_employee import get_all_employees
from Database.db_database_manager import check_permission
from Database.db_form_response import get_employee_evaluation_for_campaign, get_evaluations_for_employee, get_ai_review, save_ai_review
from pydantic import BaseModel, Field


def format_review_header(employee, position_acquired_date, campaign_name=None, eval_date="Nincs adat"):
    """Generate markdown header for review display."""
    header = (
        f"### Név: **{employee['first_name']} {employee['last_name']}**\n" +
        f"### Pozíció: **{employee['position']}"
    )
    
    if position_acquired_date and position_acquired_date != "Nincs adat":
        header += f"** ({position_acquired_date.split()[0]} óta)\n"
    else:
        header += "**\n"

    
    groups_str = ", ".join(employee.get("groups", [])) if employee.get("groups") else "Nincs"
    header += f"### Munkakör(ök): **{groups_str}**\n" + f"### Értékelés dátuma: **{eval_date}**\n"
    
    header += f"### Kampány: **{campaign_name}**\n---\n\n"

    
    return header


def employee_list_view():
    with st.spinner("Loading..."):
        st.title("AI reviews")

        all_employees = get_all_employees()

        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            st.header("Employee List", text_alignment="left")
            
        st.divider()

        if all_employees:
            col1, col2, col3, col4, col5 = st.columns([1, 3, 3, 3, 2])
            with col1:
                st.caption("**ID**", text_alignment="left")
            with col2:
                st.caption("**Name**", text_alignment="left")
            with col3:
                st.caption("**Email**", text_alignment="left")
            with col4:
                st.caption("**Campaign**", text_alignment="left")
            with col5:
                st.caption("**Actions**", text_alignment="center")

            for employee in all_employees:
                col1, col2, col3, col4, col5 = st.columns([1, 3, 3, 3, 2], vertical_alignment="center")
                with col1:
                    st.write(f"{employee['id']}")
                with col2:
                    st.write(f"**{employee['first_name']} {employee['last_name']}**")
                with col3:
                    st.write(employee['email'])
                with col4:
                    campaigns = get_all_campaigns()
                    campaign_options = [f"{c[1]}" for c in campaigns]
                    campaign_map = {c[1]: c[0] for c in campaigns}  # map name to ID
                    selected_campaign = st.selectbox("campaign", campaign_options, key=f"campaign_{employee['id']}", label_visibility="collapsed")
                with col5:
                    if st.button("Get Review", key=f"review_{employee['id']}", use_container_width=True, disabled=not check_permission("create")):
                        campaign_id = campaign_map.get(selected_campaign)
                        set_state(review_view="review", current_employee_id=employee['id'], current_campaign_id=campaign_id)
        else:
            st.info("No employees found.")

def review_view():

    if st.button("← Back to employee list"):
        set_state(review_view="list", current_employee_id=None, current_campaign_id=None)

    employee_id = st.session_state.current_employee_id
    campaign_id = st.session_state.get("current_campaign_id")
    
    if not employee_id:
        st.error("No employee selected.")
        return
    
    if not campaign_id:
        st.error("No campaign selected.")
        return

    # fetch employee details for context
    all_employees = get_all_employees()
    employee = next((e for e in all_employees if e['id'] == employee_id), None)
    if not employee:
        st.error("Employee not found.")
        return

    campaign = get_campaign_by_id(campaign_id)
    campaign_name = campaign[1] if campaign else "Nincs adat"
    position_acquired_date = employee.get("position_acquired_date", "Nincs adat")

    st.title(f"AI review for {employee['first_name']} {employee['last_name']}")

    # Get campaign-specific evaluations
    evals = get_employee_evaluation_for_campaign(employee_id, campaign_id)
    all_evals = get_evaluations_for_employee(employee_id)
    eval_date = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S") if evals else "Nincs adat"
    groups_str = ", ".join(employee.get("groups", [])) if employee.get("groups") else "Nincs"
    # Check if we already have a generated review that is up to date
    evals_json = json.dumps(evals, ensure_ascii=False, sort_keys=True)
    evals_hash = hashlib.sha256(evals_json.encode('utf-8')).hexdigest()
    
    saved_review = get_ai_review(employee_id)

    force_regenerate = st.session_state.get("force_regenerate", False) or st.session_state.get("force_regenerate_bottom", False)

    if saved_review and saved_review[1] == evals_hash and not force_regenerate:
        eval_date = saved_review[3] if len(saved_review) > 3 and saved_review[3] else eval_date
        st.markdown(
                format_review_header(employee, position_acquired_date, campaign_name, eval_date=eval_date) +
                saved_review[0]
            )
        st.info(f"Betöltve a gyorsítótárból")
        st.button("Regenerate Review", key="force_regenerate")
        return

    st.divider()
    
    with st.spinner("Generating AI review..."):
        try:
            # Start the local Phoenix app and automatically instrument LangChain
            session = px.launch_app()
            tracer_provider = register(project_name="Onlab", auto_instrument=True)
            LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

            # Only open webbrowser if this URL hasn't been opened yet
            if "opened_urls" not in st.session_state:
                st.session_state.opened_urls = set()
            
            if session.url not in st.session_state.opened_urls:
                webbrowser.open(session.url)
                st.session_state.opened_urls.add(session.url)

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
                model="openai/gpt-oss-20b:free", #350 tk 6s
                #model="arcee-ai/trinity-large-preview:free", #5500 tk, 1m 18s 
                #model= "openrouter/owl-alpha", #8562 tk, 1m 37s 
                #model= "z-ai/glm-4.5-air:free", #7484 tk, 2m 19s

                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                max_retries=5, # Automatically retry on 429 rate limit errors
            )

            @tool
            def fetch_evaluations_across_all_campaigns(employee_id: int) -> str:
                """Get all evaluations and reviews submitted by other employees for a specific employee across all the campaigns."""
                return json.dumps(get_evaluations_for_employee(employee_id), ensure_ascii=False)

            @tool
            def fetch_evaluations_for_campaign(employee_id: int, campaign_id: int) -> str:
                """Get all evaluations and reviews submitted by other employees for a specific employee in a specific campaign."""
                return json.dumps(get_employee_evaluation_for_campaign(employee_id, campaign_id), ensure_ascii=False)
        
                
            class ReviewTable(BaseModel):
                area: str = Field(description="Fejlesztendő terület megnevezése")
                program: str = Field(description="Javasolt képzés vagy módszer")
                responsible: str = Field(description="Felelős személy (Munkavállaló / Vezető)")
                deadline: str = Field(description="Határidő (Év/Hónap vagy Folyamatos)")
            
            class OutputFormat(BaseModel):
                osszesitett_teljesitmeny_szint: str = Field(description="Összesített teljesítményszint az értékelések alapján CSAK a kampányon belül, pl. 4.5/5")
                teljesitmeny_osszegzo_szovegesen: str = Field(description="2-3 mondatos összegzés az alkalmazott általános teljesítményéről az értékelések alapján, NEM szabad említeni a nevet! CSAK a kampányon belül")
                jovobeli_celok: list[str] = Field(description="Lista konkrét célokból az értékelések alapján")
                fejlesztendo_teruletek: list[ReviewTable] = Field(description="Táblázat formájú fejlesztendő területek")
                szakmai_kompetenciak: str = Field(description="Szakmai készségek és azok szintje az értékelések alapján CSAK a kampányon belül")
                kerdesek_valaszok: dict[str, str] = Field(description="Szótár ahol kulcs=kérdés, érték=összegzett válasz és pontszám CSAK a kampányon belül")
                osszesitett_ertekeles_szovegesen: str = Field(description="Végső konklúzió, kollégák által adott szöveges visszajelzések szintézise CSAK a kampányon belül")
                fejlodes_az_osszes_kampanya_alapjan: str = Field(description="Összehasonlítás az összes kampány értékelésével, miben fejlődött és miben romlott")
                osszesitett_ertekeles_osszes_kampanya: str = Field(description="Összesített pontszám vagy szint az ÖSSZES kampány alapján")

            tools = [fetch_evaluations_across_all_campaigns, fetch_evaluations_for_campaign]

            agent = create_agent(llm, tools, system_prompt=(
                                "You are an expert HR evaluation assistant. Your sole purpose is to process peer evaluations "
                                "and output a highly structured Markdown report in Hungarian following the exact template structure.\n\n"
                                "CRITICAL INSTRUCTIONS:\n"
                                "1. You MUST use `fetch_evaluations_for_campaign` to get the specific campaign data.\n"
                                "2. You MUST use `fetch_evaluations_across_all_campaigns` to get all campaign data for comparison.\n"
                                "3. Output MUST follow this EXACT structure with these headers:\n"
                                "   #### Összesített teljesítményszint\n"
                                "   #### Teljesítmény összegző értékelése szövegesen\n"
                                "   #### Jövőbeli célok\n"
                                "   #### Fejlesztendő terület (with Markdown table)\n"
                                "   #### Szakmai kompetenciák\n"
                                "   #### Kérdések és a válaszok egyesével összegezve (Pontozott értékelés)\n"
                                "   #### Összesített értékelés szövegesen az értékelések alapján\n"
                                "   #### Eddigi értékelésekhez képest ebben a kampányban\n"
                                "   #### Összesített értékelés a többi kampány alapján\n"
                                "4. You MUST completely omit the employee's name from the final output.\n"
                                "5. Output ONLY the filled Markdown template with the exact headers. Do not include conversational filler, greetings, or explanations.\n"
                                "6. Fill every section with relevant data. If data is missing, use 'Nincs adat'.\n"
                                "7. For the table in 'Fejlesztendő terület', use valid Markdown format with pipes (|).\n"
                                "8. If there are insufficient evaluations, output: 'Nincs elegendő adat az értékeléshez.'"
            ))

            response = agent.invoke(
                {"messages": [{"role": "user", "content": f"Generate a detailed AI review for Employee ID: {employee_id} in Campaign ID: {campaign_id}. Use the template provided and include sections for campaign-specific evaluation and comparison with all other campaigns. Include all sections from the template filled with relevant data."}]}
            )
            
            review_text = response["messages"][-1].content
            review_date = save_ai_review(employee_id, review_text, evals_hash, eval_date)
            
            st.markdown(
                format_review_header(employee, position_acquired_date, campaign_name, eval_date=eval_date) +
                review_text
            )

            st.button("Regenerate Review", key="force_regenerate_bottom")

            st.success(f"Értékelés sikeresen generálva: {review_date}")
                
        except Exception as e:
            st.error(f"Failed to generate review: {e}")
