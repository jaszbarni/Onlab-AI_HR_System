import streamlit as st
import random
import uuid
from database_manager import get_all_employees, get_all_groups, add_form_assignments

def show_assign_group(form_id):
    """Show the view to assign a group to a form."""

    if st.button("← Back"):
        st.session_state.campaigns_view = "campaign_forms"
        
        # Clear matrix state
        keys_to_delete = [
            k for k in st.session_state 
            if k.startswith('emp_select_') or k.startswith('cell_') or 
            k == 'num_select_boxes' or k == 'group_select' or k == 'auto_eval'
        ]
        for k in keys_to_delete:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()

    st.title("Assign Group to Form")
    
    st.divider()

    all_groups = get_all_groups()
    all_employees = get_all_employees()

    col1, col2, col3 = st.columns([0.3, 0.3, 0.4], border=True)
    with col1:
        st.write("Select a group")
        st.selectbox(
            label="Select group",
            options=["No group"] + all_groups,
            key="group_select",
            placeholder="Select a group",
            label_visibility="collapsed"
        )
    with col2:
        st.write("Everyone has to have self-evaluation")
        st.selectbox(
            label="self eval",
            options=["No", "Yes"],
            key="self_eval",
            label_visibility="collapsed"
        )
    with col3:
        st.write("Random evaluation | How many evaulations per person?")
        sub_col1, sub_col2 = st.columns([0.4, 0.6])
        with sub_col1:
            st.selectbox(
                label="auto eval",
                options=["No", "Yes"],
                key="auto_eval",
                label_visibility="collapsed"
                )
        with sub_col2:
            st.number_input(
                label="How many",
                min_value=0,
                max_value=len(all_employees)-1, #-1 because of the self eval
                key="num_select_boxes",
                disabled=st.session_state.get("auto_eval") == "No",
                label_visibility="collapsed",
                step=1,
                )

    selected_group = st.session_state.get("group_select")
    employees = []

    if selected_group and selected_group != "No group":
        employees += [emp for emp in all_employees if selected_group in emp.get('groups', [])]

    if employees == []:
        employees = all_employees
    
    employee_names = [f"{employee['first_name']} {employee['last_name']}" for employee in employees]

    # --- Initialize Manual Selection State ---
    if 'employee_selections' not in st.session_state:
        st.session_state.employee_selections = []
        
    if 'employee_slot_keys' not in st.session_state:
        st.session_state.employee_slot_keys = [str(uuid.uuid4()) for _ in st.session_state.employee_selections]

    # --- Handle auto random selection ---
    is_auto_eval = st.session_state.get("auto_eval") == "Yes"

    if 'was_auto_eval' not in st.session_state:
        st.session_state.was_auto_eval = not is_auto_eval

    switched_to_auto = is_auto_eval and not st.session_state.was_auto_eval
    switched_from_auto = not is_auto_eval and st.session_state.was_auto_eval
    
    if switched_from_auto:
        st.session_state.employee_selections = [""] # Reset when switching off auto
        st.session_state.employee_slot_keys = [str(uuid.uuid4())] # Reset keys
        for key in list(st.session_state.keys()):
            if key.startswith("cell_"):
                st.session_state[key] = False 

    num_boxes_changed = False
    if is_auto_eval:
        if 'last_num_boxes' not in st.session_state:
            st.session_state.last_num_boxes = -1
        if st.session_state.last_num_boxes != st.session_state.get("num_select_boxes", 0):
            num_boxes_changed = True
            st.session_state.last_num_boxes = st.session_state.get("num_select_boxes", 0)

    if is_auto_eval and (switched_to_auto or num_boxes_changed):
        num_to_select = int(st.session_state.get("num_select_boxes", 0))
        
        # Clear all previous evaluation selections before re-calculating
        for key in list(st.session_state.keys()):
            if key.startswith("cell_"):
                # FIX: Force to False instead of deleting
                st.session_state[key] = False

        if switched_to_auto:
            # Automatically select all employees only when switching to auto mode
            st.session_state.employee_selections = employee_names.copy()
            st.session_state.employee_slot_keys = [str(uuid.uuid4()) for _ in employee_names]
        
        selected_employees = list(dict.fromkeys([s for s in st.session_state.get("employee_selections", []) if s]))
        
        if num_to_select > 0 and selected_employees:
            for filler_emp in selected_employees:
                possible_targets = [emp for emp in selected_employees if emp != filler_emp]
                num_evals = min(num_to_select, len(possible_targets))
                if num_evals > 0:
                    targets_to_eval = random.sample(possible_targets, num_evals)
                    for target_emp in targets_to_eval:
                        st.session_state[f"cell_{filler_emp}_{target_emp}"] = True

    st.session_state.was_auto_eval = is_auto_eval

    col1, col2 = st.columns([0.3, 0.7], border=True)

    with col1:
        st.subheader("Select Employees")

        def add_employee_slot():
            st.session_state.employee_selections.append("")
            st.session_state.employee_slot_keys.append(str(uuid.uuid4()))

        def remove_employee_slot(index):
            st.session_state.employee_selections.pop(index)
            st.session_state.employee_slot_keys.pop(index)

        def sync_selection(index, key):
            st.session_state.employee_selections[index] = st.session_state[key]

        all_current_selections = {s for s in st.session_state.employee_selections if s}

        for i, selection in enumerate(st.session_state.employee_selections):
            sub_col1, sub_col2 = st.columns([0.80, 0.20])
            
            slot_id = st.session_state.employee_slot_keys[i]
            
            with sub_col1:
                other_selections = all_current_selections - {selection}
                available_options = [name for name in employee_names if name not in other_selections]
                
                try:
                    default_index = ([""] + available_options).index(selection)
                except ValueError:
                    default_index = 0
                
                widget_key = f"emp_select_{slot_id}"
                st.selectbox(
                    label=f"Employee {i+1}",
                    options=[""] + available_options,
                    key=widget_key,
                    index=default_index,
                    label_visibility="collapsed",
                    on_change=sync_selection,
                    args=(i, widget_key),
                )

            with sub_col2:
                st.button(label="❌", key=f"remove_emp_{slot_id}", on_click=remove_employee_slot, args=(i,))

        st.button("Add employee", on_click=add_employee_slot)

    with col2:

        st.subheader("Evaluation Matrix", text_alignment="center", divider="gray")

        header_col1, header_col2 = st.columns([0.25, 0.75])
        with header_col1:
            st.caption("**Form Filler ↓**")
        with header_col2:
            st.caption("**Target Employee →**")
            

        selected_employees = [s for s in st.session_state.employee_selections if s]
        selected_employees = list(dict.fromkeys(selected_employees)) 

        if selected_employees:
            matrix_employees = list(selected_employees)

            # Header row
            header_cols = st.columns(len(matrix_employees) + 1)
            header_cols[0].write("")
            for i, target_emp in enumerate(matrix_employees):
                header_cols[i+1].write(target_emp)

            def Get_employee_role(target_emp):
                target_emp_data = next((emp for emp in all_employees if f"{emp['first_name']} {emp['last_name']}" == target_emp), None)
                role = "Peer"
                if target_emp_data:
                    role = target_emp_data.get("role") or "Peer"
                return role

            
            role_colors = {}
            color_palette = [
                "red", "orange", "yellow", "blue", "green", "violet"
            ]
            next_color_index = 0

            # Matrix rows
            for filler_emp in matrix_employees:
                row_cols = st.columns(len(matrix_employees) + 1)
                row_cols[0].write(filler_emp)
                
                for i, target_emp in enumerate(matrix_employees):
                    with row_cols[i+1]:
                        in_row_col1, in_row_col2 = st.columns([0.01, 0.9], vertical_alignment="center")
                        
                        if filler_emp == target_emp:
                            with in_row_col1:
                                if st.session_state.get("self_eval") == "Yes":
                                    st.session_state[f"cell_{filler_emp}_{target_emp}"] = True
                                    st.checkbox("", key=f"cell_{filler_emp}_{target_emp}", disabled=True)
                                else:
                                    st.checkbox("", key=f"cell_{filler_emp}_{target_emp}")
                            if st.session_state.get(f"cell_{filler_emp}_{target_emp}") == True:
                                with in_row_col2:
                                    st.badge("Self-evaluation", color="grey")
                        else:
                            with in_row_col1:
                                st.checkbox("", key=f"cell_{filler_emp}_{target_emp}")
                            if st.session_state.get(f"cell_{filler_emp}_{target_emp}") == True:
                                with in_row_col2:
                                    role = Get_employee_role(target_emp)
                                    if role not in role_colors:
                                        role_colors[role] = color_palette[next_color_index]
                                        next_color_index = (next_color_index + 1) % len(color_palette)
                                    st.badge(role, color=role_colors[role])
            st.divider()

            if st.button("Assign Group", type="primary"):
                send_form = []
                for filler_emp in matrix_employees:
                    for target_emp in matrix_employees:
                        if st.session_state.get(f"cell_{filler_emp}_{target_emp}"):
                            send_form.append({
                                "form_filler": filler_emp,
                                "target": target_emp,
                                "form_type": Get_employee_role(target_emp)
                            })
                
                add_form_assignments(form_id, send_form)
                st.session_state.send_form = send_form
                st.success(f"{len(st.session_state.send_form)} assignments prepared and saved to database.")
                st.write(st.session_state.send_form)
        else:
            st.info("No employees selected.")