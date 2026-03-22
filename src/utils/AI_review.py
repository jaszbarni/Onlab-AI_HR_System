import streamlit as st
from database_manager import get_all_employees


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
                    pass # We will wire this up later to open the AI review screen
    else:
        st.info("No employees found.")