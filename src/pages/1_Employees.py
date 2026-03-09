import streamlit as st
from database_manager import(
    get_all_employees, update_employee_role, ROLES, check_permission, delete_employee, 
    add_group_to_employee, remove_group_from_employee, get_all_groups, add_group, delete_group
)
from utils.common import delete_confirmation_dialog

st.set_page_config(layout="wide")

if "view" not in st.session_state:
    st.session_state.view = "employees"

try:
    with open("Resources/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.error("CSS file not found. Please make sure 'style.css' is in the same folder.")


# Dialog for managing all groups
@st.dialog("Manage Groups")
def group_manager():
    st.write("**Create a new group:**")
    col1, col2 = st.columns([3, 1])
    with col1:
        custom_group = st.text_input(
            "New group name",
            key="new_group_input",
            label_visibility="collapsed",
            placeholder="Enter new group name"
        )
    with col2:
        if st.button("Create", key="create_group_btn", use_container_width=True):
            if custom_group.strip():
                add_group(custom_group.strip())
                st.success(f"Group '{custom_group.strip()}' created!")
                st.rerun()
            else:
                st.error("Group name cannot be empty")
    
    st.divider()
    
    st.write("**All Groups:**")
    all_groups = get_all_groups()
    
    if all_groups:
        for group in all_groups:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"• {group}")
            with col2:
                if st.button("Delete", key=f"delete_group_{group}", use_container_width=True):
                    delete_group(group)
                    st.success(f"Group '{group}' deleted!")
                    st.rerun()
    else:
        st.info("No groups created yet")


#if check_permission("update"):
col1, col2 = st.columns([4, 1])
with col1:
    st.header("Employees")
with col2:
    if st.button("Manage Groups", type="secondary", use_container_width=True):
        group_manager()

st.divider()

# Dialog for editing employee groups
@st.dialog("Edit Employee Groups")
def edit_groups_dialog(employee_id, employee_name, current_groups):
    all_groups = get_all_groups()
    
    st.write(f"Managing groups for **{employee_name}**")
    st.divider()
    
    # Display current groups
    st.subheader("Current Groups")
    if current_groups:
        for group in current_groups:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"• {group}")
            with col2:
                if st.button("Remove", key=f"remove_{employee_id}_{group}", use_container_width=True):
                    remove_group_from_employee(employee_id, group)
                    st.rerun()
        
    st.divider()
    
    # Add new group
    st.subheader("Add New Group")
    available_groups = [g for g in all_groups if g not in current_groups]
    
    # Option 1: Select from existing groups
    if available_groups:
        col1, col2 = st.columns([3, 1])
        with col1:
            new_group = st.selectbox(
                "Select a group",
                options=available_groups,
                key=f"available_groups_{employee_id}",
                label_visibility="collapsed"
            )
        with col2:
            if st.button("Add", key=f"add_btn_{employee_id}", use_container_width=True):
                add_group_to_employee(employee_id, new_group)
                st.rerun()
    else:
        st.info("No groups available")


employees = get_all_employees()

col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    st.caption("**ID**", text_alignment="left")
with col2:
    st.caption("**Name**", text_alignment="left")
with col3:
    st.caption("**Email**", text_alignment="left")
with col4:
    st.caption("**Groups**", text_alignment="left")
with col5:
    st.caption("**Role**", text_alignment="center")
with col6:
    st.caption("**Actions**", text_alignment="center")

if employees:
    for employee in employees:
        col1, col2, col3, col4, col5, col6 = st.columns(6, vertical_alignment="center")
        with col1:
            st.write(f"{employee['id']}")
        with col2:
            st.write(f"**{employee['first_name']} {employee['last_name']}**")
        with col3:
            st.write(employee['email'])
        with col4:
            with st.container(border=True):
                if employee['groups']:
                    for group in employee['groups']:
                        st.write(f"  • {group}")
                else:
                    st.write("No groups assigned")
        with col5:
            disabled = True
            #if check_permission("update"):
            disabled = False

            role_options = list(ROLES.keys())
            current_role_index = 0
            if employee['role'] in role_options:
                current_role_index = role_options.index(employee['role'])
            
            new_role = st.selectbox(
                "Role",
                options=role_options,
                index=current_role_index,
                key=f"role_{employee['id']}",
                label_visibility="collapsed",
                disabled=disabled
            )
            if new_role != employee['role']:
                update_employee_role(employee['id'], new_role)
                st.rerun()
        with col6:
            col_edit, col_delete = st.columns(2)
            #if check_permission("update"):
            with col_edit:
                if st.button(label="Edit groups", key=f"edit_{employee['id']}"):
                    edit_groups_dialog(employee['id'], f"{employee['first_name']} {employee['last_name']}", employee['groups'])
            #if check_permission("delete"):
            with col_delete:
                if st.button(label="❌", key=f"delete_{employee['id']}"):
                    delete_confirmation_dialog("employee", delete_employee, employee['id'])

else:
    st.info("No employees found.")