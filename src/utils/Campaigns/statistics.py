
import streamlit as st
import pandas as pd
import altair as alt
from utils.common import set_state
from classes.form_template_class import FormTemplate
from Database.forms import get_forms_by_campaign, get_assignments_by_form


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
                        if q_type == "1-10 Rating":
                            score = score / 2.0
                        data.append({
                            "Form": form[1],
                            "Employee": target_name,
                            "Question": q_text,
                            "Score": score
                        })
                    except ValueError:
                        pass
    
    if data:
        df = pd.DataFrame(data)
        
        st.subheader("Campaign Overview: Overall Employee Scores")
        df_campaign_summary = df.groupby("Employee")["Score"].mean().reset_index()
        
        campaign_chart = alt.Chart(df_campaign_summary).mark_bar().encode(
            x=alt.X('Employee:N', title='', sort='-y', axis=alt.Axis(labelAngle=-45)),
            y=alt.Y('Score:Q', title='Overall Mean Score').scale(domain=(0, 5)),
            color=alt.Color('Employee:N', legend=None),
            tooltip=[alt.Tooltip('Employee:N'), alt.Tooltip('Score:Q', format='.2f')]
        ).properties(height=400)
        
        st.altair_chart(campaign_chart, use_container_width=True)
        st.divider()

        for form_name, group_df in df.groupby("Form"):
            st.subheader(f"Summarized Evaluations: {form_name}")
            
            # Group by Question to calculate the summarized mean score
            df_summary = group_df.groupby("Question")["Score"].mean().reset_index()

            chart = alt.Chart(df_summary).mark_bar().encode(
                x=alt.X('Score:Q', title='Mean Score', axis=alt.Axis(tickMinStep=1)).scale(domain=(0, 5)),
                y=alt.Y('Question:N', title='', axis=alt.Axis(labelLimit=0)),
                color=alt.Color('Question:N', legend=None)
            )
            st.altair_chart(chart, use_container_width=True)
            
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Summarized Statistics")
                df_summary_disp = df_summary.set_index("Question")
                st.dataframe(df_summary_disp, use_container_width=True)
            with col2:
                st.subheader("Score Distribution")
                point_chart = alt.Chart(group_df).mark_circle(size=300).encode(
                    x=alt.X('Score:Q', title='Score', axis=alt.Axis(tickMinStep=1)).scale(domain=(0, 5)),
                    y=alt.Y('Question:N', title='', axis=alt.Axis(labelLimit=0)),
                    opacity=alt.Opacity('count()', title='', scale=alt.Scale(range=[0.3, 1.0]), legend=alt.Legend(tickMinStep=1)),
                    color=alt.value('Yellow'),
                    tooltip=[alt.Tooltip('Question:N'), alt.Tooltip('Score:Q'), alt.Tooltip('count()', title='Count')]
                )
                st.altair_chart(point_chart, use_container_width=True)
                
            st.divider()
    else:
        st.info("No rating evaluations have been submitted yet.")
