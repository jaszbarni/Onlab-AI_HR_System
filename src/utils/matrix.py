import streamlit as st
from database_manager import get_all_employees, get_all_groups, assign_group_to_form

def show_assign_group(form_id):
    """Show the view to assign a group to a form."""
    st.title("Assign Group to Form")

    if st.button("← Back"):
        st.session_state.campaigns_view = "campaign_forms"
        
        # Clear matrix state
        keys_to_delete = [k for k in st.session_state if k.startswith('emp_select_') or k == 'num_select_boxes']
        for k in keys_to_delete:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()

    

    st.divider()

    all_groups = get_all_groups()
    employees = get_all_employees()
    employee_names = [f"{employee['first_name']} {employee['last_name']}" for employee in employees]



    if 'num_select_boxes' not in st.session_state:
        st.session_state.num_select_boxes = 1

    col1, col2 = st.columns([0.3, 0.7])

    with col1:
        st.subheader("Select Employees")

        # Get all unique selections from the session state
        all_selections = set()
        for i in range(st.session_state.num_select_boxes):
            employee = st.session_state.get(f"emp_select_{i}")
            if employee:
                all_selections.add(employee)

        for i in range(st.session_state.num_select_boxes):
            sub_col1, sub_col2 = st.columns([0.85, 0.15])
            with sub_col1:
                current_selection = st.session_state.get(f"emp_select_{i}")
                
                other_selections = all_selections - {current_selection}
                available_options = [name for name in employee_names if name not in other_selections]
                
                st.selectbox(
                    label=f"Employee {i+1}",
                    options=[""] + available_options,
                    key=f"emp_select_{i}",
                    label_visibility="collapsed"
                )
            with sub_col2:
                if st.button("X", key=f"remove_emp_{i}", type="primary"):
                    for j in range(i, st.session_state.num_select_boxes - 1):
                        st.session_state[f"emp_select_{j}"] = st.session_state.get(f"emp_select_{j+1}", "")
                    
                    last_key = f"emp_select_{st.session_state.num_select_boxes - 1}"
                    if last_key in st.session_state:
                        del st.session_state[last_key]

                    st.session_state.num_select_boxes -= 1
                    st.rerun()

        if st.button("+ Add employee"):
            st.session_state.num_select_boxes += 1
            st.rerun()

    with col2:
        st.subheader("Evaluation Matrix")

        selected_employees = []
        for i in range(st.session_state.num_select_boxes):
            employee = st.session_state.get(f"emp_select_{i}")
            if employee:
                selected_employees.append(employee)
        
        selected_employees = list(dict.fromkeys(selected_employees))

        if selected_employees:
            
            matrix_employees = list(selected_employees)

            # Header row
            header_cols = st.columns(len(matrix_employees) + 1)
            header_cols[0].write("")
            for i, target_emp in enumerate(matrix_employees):
                header_cols[i+1].write(target_emp)

            # Matrix rows
            for filler_emp in matrix_employees:
                row_cols = st.columns(len(matrix_employees) + 1)
                row_cols[0].write(filler_emp)
                
                for i, target_emp in enumerate(matrix_employees):
                    with row_cols[i+1]:
                        st.checkbox("", key=f"cell_{filler_emp}_{target_emp}")
            
            st.divider()

            if st.button("Assign Group", type="primary"):
                send_form = []
                for filler_emp in matrix_employees:
                    for target_emp in matrix_employees:
                        if st.session_state.get(f"cell_{filler_emp}_{target_emp}"):
                            send_form.append({
                                "form_filler": filler_emp,
                                "target": target_emp
                            })
                
                st.session_state.send_form = send_form
                st.success(f"{len(st.session_state.send_form)} employees assigned")
                st.write(st.session_state.send_form)
        else:
            st.info("No employees selected.")