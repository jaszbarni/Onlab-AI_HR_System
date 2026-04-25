import phoenix as px
from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor
import webbrowser
import os
import json
from database_manager import add_question, get_company_values
from dotenv import load_dotenv, find_dotenv
from classes.form_template_class import FormTemplate
import streamlit as st


def use_AI_questions(form_id, form_name, form_desc, num_of_questions):

    # Start the local Phoenix app and automatically instrument LangChain
    session = px.launch_app()
    tracer_provider = register(project_name="Onlab", auto_instrument=True)
    LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
    
    webbrowser.open(session.url)

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
        You are a Senior Strategic HR Consultant specializing in performance management and organizational development.
        ### Language
        You MUST use Hungarian language in your final responses.
        
        ### Context
        The company core values are: {comp_values}
        The target position for this evaluation is: {form_name}
        Role Description: {form_desc}

        ### Objective
        Generate exactly {num_of_questions} NEW, unique evaluation questions.
        The questions must bridge the gap between the **Company Values** and the specific **Job Responsibilities** of a {form_name}. 

        ### Guidelines
        1. **Role Specificity:** Do not use generic questions. If the role is "Developer," ask about code quality or collaboration. If it is "Sales," ask about client relationships.
        2. **Behavioral Focus:** For Rating questions, the description should include 3-4 bullet points of observable behaviors (e.g., "Always meets deadlines," "Proactively suggests improvements").
        3. **Avoid Duplication:** You MUSTN'T replicate these existing questions or their title or description: {existing_questions}.
        4. **Language:** Generate the response in the same language as the Title and Description provided.

        ### Output Format
        Return ONLY a valid JSON array. Each object must contain:
        - `question_text`: Concise title (max 40 chars).
        - `question_description`: Bulleted list of behavioral indicators and a concluding sentence.
        - `question_type`: Choose strictly from ["Text Box", "0-5 Rating", "1-10 Rating"].

        ### Example Structure
        [
          {{
            "question_text": "Munkavégzés minősége és hatékonysága",
            "question_description": "• Ismeri és teljesíti a munkaköri elvárásokat. (minőségi, mennyiségi, határidők betartása)\n
                                    • Plusz feladatokat is képes hatékonyan megoldani.\n
                                    • Önállóan és fókuszáltan dolgozik, terhelés alatt is megtartja a teljesítményét.\n
                                    • Biztonsággal használja a szükséges szoftvereket, vállalatirányítási rendszereket",
            "question_type": "0-5 Rating"
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
                temperature=0.2
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