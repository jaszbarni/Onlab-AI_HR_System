import streamlit as st
import random
import uuid
import difflib
from database_manager import(
    get_all_employees, get_all_form_templates, get_all_groups, 
    add_form_assignments, get_forms_by_campaign, create_form_from_template
)
from utils.common import set_state

def show_assign_group(campaign_id):
    """Show the view to assign a group to a campaign."""

    if st.button("← Back"):
        
        # Clear matrix state
        keys_to_delete = [
            k for k in st.session_state 
            if k.startswith('emp_select_') or k.startswith('cell_') or 
            k == 'num_select_boxes' or k == 'group_select' or k == 'auto_eval'
        ]
        for k in keys_to_delete:
            if k in st.session_state:
                del st.session_state[k]
        set_state(campaigns_view="campaign_forms")

    st.title("Assign Group to Form")
    
    st.divider()

    all_groups = get_all_groups()
    all_employees = get_all_employees()

    # --- Initialize Manual Selection State ---
    if 'employee_selections' not in st.session_state:
        st.session_state.employee_selections = []
        
    if 'employee_slot_keys' not in st.session_state:
        st.session_state.employee_slot_keys = [str(uuid.uuid4()) for _ in st.session_state.employee_selections]

    current_selections = list(dict.fromkeys([s for s in st.session_state.employee_selections if s]))
    max_evals = max(0, len(current_selections) - 1)

    if st.session_state.get("num_select_boxes", 0) > max_evals:
        st.session_state.num_select_boxes = max_evals

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
                max_value=max_evals,
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

    # --- Handle auto random selection ---
    is_auto_eval = st.session_state.get("auto_eval") == "Yes"

    if 'was_auto_eval' not in st.session_state:
        st.session_state.was_auto_eval = not is_auto_eval

    switched_to_auto = is_auto_eval and not st.session_state.was_auto_eval
    switched_from_auto = not is_auto_eval and st.session_state.was_auto_eval
    
    if switched_from_auto:
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

        position_colors = {}
        position_color_palette = [
            "red", "orange", "blue", "green", "violet"
        ]
        next_color_index = 0

        def get_position_color(position):
            nonlocal next_color_index
            if position not in position_colors:
                position_colors[position] = position_color_palette[next_color_index % len(position_color_palette)]
                next_color_index += 1
            return position_colors[position]

        def Get_employee_position(target_emp):
            target_emp_data = next((emp for emp in all_employees if f"{emp['first_name']} {emp['last_name']}" == target_emp), None)
            position = "Peer"
            if target_emp_data:
                position = target_emp_data.get("position") or "Peer"
            return position

        if selected_employees:
            matrix_employees = list(selected_employees)

            # Fetch templates once
            if campaign_id:
                campaign_forms_data = get_forms_by_campaign(campaign_id)
            else:
                campaign_forms_data = get_all_form_templates()
                
            base_form_templates = [{"id": t[0], "name": t[1]} for t in campaign_forms_data]

            # Header row
            header_cols = st.columns(len(matrix_employees) + 1, gap="xsmall")
            header_cols[0].write("")
            for i, target_emp in enumerate(matrix_employees):
                position = Get_employee_position(target_emp)
                with header_cols[i+1]:
                    name_col1, name_col2 = st.columns(gap=None, spec=2)
                    with name_col1:
                        st.write(target_emp)
                    with name_col2:
                        st.badge(f"{position}", color=get_position_color(position))

            # Matrix rows
            for filler_emp in matrix_employees:
                row_cols = st.columns(len(matrix_employees) + 1, gap="xsmall")
                position = Get_employee_position(filler_emp)
                with row_cols[0]:
                    name_col1, name_col2 = st.columns(gap=None, spec=2)
                    with name_col1:
                        st.write(filler_emp)
                    with name_col2:
                        st.badge(f"{position}", color=get_position_color(position))
                
                for i, target_emp in enumerate(matrix_employees):
                    with row_cols[i+1]:
                        in_row_col1, in_row_col2 = st.columns([0.01, 0.9], vertical_alignment="center")
                        
                        with in_row_col1:
                            if filler_emp == target_emp and st.session_state.get("self_eval") == "Yes":
                                st.session_state[f"cell_{filler_emp}_{target_emp}"] = True
                                st.checkbox("", key=f"cell_{filler_emp}_{target_emp}", disabled=True)
                            else:
                                st.checkbox("", key=f"cell_{filler_emp}_{target_emp}")

                        if st.session_state.get(f"cell_{filler_emp}_{target_emp}"):
                            with in_row_col2:
                                if filler_emp == target_emp:
                                    st.badge("Self-evaluation", color="grey")
                                    target_position = "Self-evaluation"
                                else:   
                                    cell_form_templates = list(base_form_templates)
                                    target_position = Get_employee_position(target_emp)
                                
                                    # Exclude self evaluation templates from peer evaluation options
                                    cell_form_templates = [ft for ft in cell_form_templates if "self" not in ft["name"].lower()]
                                    
                                    template_names = [ft["name"] for ft in cell_form_templates]
                                    
                                    # Find the best match for the position among template names
                                    best_match_name_list = difflib.get_close_matches(target_position, template_names, n=1, cutoff=0.1)
                                    
                                    if best_match_name_list:
                                        best_match_name = best_match_name_list[0]
                                        # Reorder the templates to put the best match first
                                        best_match_template = next((t for t in cell_form_templates if t["name"] == best_match_name), None)
                                        if best_match_template:
                                            cell_form_templates.remove(best_match_template)
                                            cell_form_templates.insert(0, best_match_template)

                                    st.selectbox(
                                        label="form type",
                                        options=cell_form_templates,
                                        format_func=lambda x: x["name"],
                                        label_visibility="collapsed",
                                        key=f"form_type_{filler_emp}_{target_emp}"
                                    )

            if st.button("Assign Group", type="primary"):
                send_form = []
                self_eval_template = next((t for t in base_form_templates if "self" in t["name"].lower()), None)
                
                # Auto-create self-eval form for this campaign if it doesn't exist
                if not self_eval_template and campaign_id:
                    all_templates = get_all_form_templates()
                    global_self_eval = next((t for t in all_templates if "self" in t[1].lower()), None)
                    if global_self_eval:
                        new_form_id = create_form_from_template(global_self_eval[0], campaign_id, "System")
                        self_eval_template = {"id": new_form_id, "name": global_self_eval[1]}

                for filler_emp in matrix_employees:
                    for target_emp in matrix_employees:
                        if st.session_state.get(f"cell_{filler_emp}_{target_emp}"):
                            if target_emp == filler_emp:
                                form_type = "Self-evaluation"
                                form_id_to_assign = self_eval_template["id"] if self_eval_template else None
                            else:
                                selected_template = st.session_state.get(f"form_type_{filler_emp}_{target_emp}")
                                form_type = selected_template["name"] if selected_template else Get_employee_position(target_emp)
                                form_id_to_assign = selected_template["id"] if selected_template else None
                            
                            send_form.append({
                                "form_filler": filler_emp,
                                "target": target_emp,
                                "form_type": form_type,
                                "form_id": form_id_to_assign
                            })
                
                add_form_assignments(send_form)
                st.session_state.send_form = send_form
                st.success(f"{len(st.session_state.send_form)} assignments prepared and saved to database.")
        else:
            st.info("No employees selected.")