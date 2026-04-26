import streamlit as st
from Database.database_manager import check_permission, get_all_positions_with_permissions, get_all_positions
from Database.employee import add_employee, get_all_employees, delete_employee
from Database.groups_positions import add_group, add_position, delete_position, get_all_groups, remove_group_from_employee, update_position, add_group_to_employee, delete_group, update_employee_position
from classes.user_class import User

from utils.common import check_email_format, delete_confirmation_dialog

st.set_page_config(layout="wide", initial_sidebar_state="expanded")

if "view" not in st.session_state:
    st.session_state.view = "employees"

try:
    with open("Resources/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.error("CSS file not found. Please make sure 'style.css' is in the same folder.")

# Hide the sidebar collapse/expand buttons to fix it open
st.markdown(
    """
    <style>
        [data-testid="collapsedControl"] {display: none;}
        [data-testid="stSidebarCollapseButton"] {display: none;}
    </style>
    """,
    unsafe_allow_html=True,
)

@st.dialog("Add employee")
def add_employee_dialog():
    first_name = st.text_input(
        "First name",
        label_visibility="collapsed",
        placeholder="Enter first name"
    )
    last_name = st.text_input(
        "Last name",
        label_visibility="collapsed",
        placeholder="Enter last name"
    )
    email = st.text_input(
        "Email",
        label_visibility="collapsed",
        placeholder="Enter email"
    )

    if st.button("Save"):
        if(not check_email_format(email)):
            st.error("Invalid email format")  
        elif first_name.strip() and last_name.strip() and email.strip():
            new_user = User(
                first_name.strip(),
                last_name.strip(),
                email.strip(),
                "None"
            )
            add_employee(new_user)
            st.success("Employee added!")
            st.rerun()
        else:
            st.error("Please fill in all fields.")


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
            placeholder="Enter new group name",
            disabled=not check_permission("create")
        )
    with col2:
        if st.button("Create", key="create_group_btn", use_container_width=True, disabled=not check_permission("create")):
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
                if st.button("Delete", key=f"delete_group_{group}", use_container_width=True, disabled=not check_permission("delete")):
                    delete_group(group)
                    st.success(f"Group '{group}' deleted!")
                    st.rerun()
    else:
        st.info("No groups created yet")

@st.dialog("Manage Positions")
def position_manager():
    st.write("**Create a new position:**")
    col1, col2 = st.columns([3, 1])
    with col1:
        custom_position = st.text_input(
            "New position name",
            key="new_position_input",
            label_visibility="collapsed",
            placeholder="Enter new position name"
        )
    with col2:
        if st.button("Create", key="create_position_btn", use_container_width=True, disabled=not check_permission("create")):
            if custom_position.strip():
                add_position(custom_position.strip(), [])
                st.success(f"Position '{custom_position.strip()}' created!")
                st.rerun()
            else:
                st.error("Position name cannot be empty")
    
    st.divider()
    
    st.write("**All Positions:**")
    all_positions = get_all_positions_with_permissions()
    
    available_permissions = ["create", "read", "update", "delete"]
    
    if all_positions:
        for position_data in all_positions:
            position = position_data["name"]
            permissions = position_data["permissions"]
            
            with st.expander(f"Position: {position}"):
                st.write("**Permissions:**")
                cols = st.columns(len(available_permissions))
                new_permissions = []
                for i, perm in enumerate(available_permissions):
                    with cols[i]:
                        if st.checkbox(perm.capitalize(), value=(perm in permissions), key=f"chk_{position}_{perm}"):
                            new_permissions.append(perm)
                
                if set(new_permissions) != set(permissions):
                    update_position(position, new_permissions)
                
                st.divider()
                if st.button("Delete Position", key=f"delete_position_{position}", type="primary", use_container_width=True, disabled=not check_permission("delete")):
                    delete_position(position)
                    st.success(f"Position '{position}' deleted!")
                    st.rerun()
    else:
        st.info("No positions defined")



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
                if st.button("Remove", key=f"remove_{employee_id}_{group}", use_container_width=True, disabled=not check_permission("update")):
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
            if st.button("Add", key=f"add_btn_{employee_id}", use_container_width=True, disabled=not check_permission("update")):
                add_group_to_employee(employee_id, new_group)
                st.rerun()
    else:
        st.info("No groups available")


if check_permission("update"):
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col1:
        st.header("Employees")
    with col2:
        if st.button("Manage Positions", type="secondary", use_container_width=True, disabled=not check_permission("create")):
            position_manager()
    with col3:
        if st.button("Manage Groups", type="secondary", use_container_width=True, disabled=not check_permission("create")):
            group_manager()
    with col4:
        if st.button("Add employee", type="secondary", use_container_width=True, disabled=not check_permission("create")):
            add_employee_dialog()

st.divider()

employees = get_all_employees()

col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([0.5, 1, 2, 2, 1.5, 1, 1, 2])
with col1:
    st.caption("**ID**", text_alignment="left")
with col2:
    st.caption("**Name**", text_alignment="left")
with col3:
    st.caption("**Email**", text_alignment="left")
with col4:
    st.caption("**Groups**", text_alignment="left")
with col5:
    st.caption("**Position**", text_alignment="center")
with col6:
    st.caption("**Created At**", text_alignment="center")
with col7:
    st.caption("**Position Acquired**", text_alignment="center")
if check_permission("update"):
    with col8:
        st.caption("**Actions**", text_alignment="center")

if employees:
    for employee in employees:
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([0.5, 1, 2, 2, 1.5, 1, 1, 2], vertical_alignment="center")
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
            if check_permission("update"):
                disabled = False

            position_options = get_all_positions() + ["None"]
            
            # If the employee has a position but it's not in the DB's positions table, add it so the selectbox doesn't wipe it
            if employee['position'] and employee['position'] not in position_options:
                position_options.insert(0, employee['position'])
                
            current_position_index = 0
            if employee['position'] in position_options:
                current_position_index = position_options.index(employee['position'])
            
            new_position = st.selectbox(
                "Position",
                options=position_options,
                index=current_position_index if position_options else None,
                key=f"position_{employee['id']}",
                label_visibility="collapsed",
                disabled=disabled or not position_options
            )
            # Ensure we only update if a valid new position was selected (not None from an empty list)
            if new_position is not None and new_position != employee['position']:
                update_employee_position(employee['id'], new_position)
                st.rerun()
        with col6:
            created = employee.get('created_date')
            st.write(created.split()[0] if created else "N/A")
        with col7:
            position_acquired = employee.get('position_acquired_date')
            st.write(position_acquired.split()[0] if position_acquired else "N/A")
        with col8:
            col_edit, col_delete = st.columns(2)
            if check_permission("update"):
                with col_edit:
                    if st.button(label="Edit groups", key=f"edit_{employee['id']}", disabled=not check_permission("update")):
                        edit_groups_dialog(employee['id'], f"{employee['first_name']} {employee['last_name']}", employee['groups'])
                if check_permission("delete"):
                    with col_delete:
                        if st.button(label="❌", key=f"delete_{employee['id']}", disabled=not check_permission("delete")):
                            delete_confirmation_dialog("employee", delete_employee, employee['id'])
    
else:
    st.info("No employees found.")