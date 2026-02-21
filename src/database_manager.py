import streamlit as st
import sqlite3

# --- User Management & Permissions ---
# Role definíciók és a hozzájuk tartozó jogosultságok (CRUD)
ROLES = {
    "Leader": ["create", "read", "update", "delete"],
    "Manager": ["create", "read", "update"],
    "Employee": ["read"]
}

class User:
    def __init__(self, first_name, last_name, role, group, email):
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
        self.group = group
        self.email = email

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role}), {self.group} group, email: {self.email}"


def check_permission(permission):
    user_role = st.session_state.user.role
    if user_role in ROLES:
        return permission in ROLES[user_role]
    else:
        st.error("Invalid user role.")
        return False

# --- Database Management ---

def init_db():
    conn = sqlite3.connect("personal_data.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT NOT NULL,
                "group" TEXT,
                role TEXT NOT NULL)""")
    conn.commit()
    conn.close()

init_db()

def add_employee(user: User):
    conn = sqlite3.connect("personal_data.db")
    cursor = conn.cursor()
    cursor.execute('INSERT INTO employees (first_name, last_name, email, "group", role) VALUES (?, ?, ?, ?, ?)', #sql injection?
                   (
                       user.first_name,
                       user.last_name,
                       user.email,
                       user.group,
                       user.role
                   ))
    conn.commit()
    conn.close()

def get_all_employees():
    conn = sqlite3.connect("personal_data.db")
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM employees')
    rows = cursor.fetchall()
    conn.close()
    
    employees = []
    for row in rows:
        employees.append({
            "id": row[0],
            "first_name": row[1],
            "last_name": row[2],
            "email": row[3],
            "group": row[5],
            "role": row[4]
        })
        
    return employees

def update_employee_role(employee_id, new_role):
    """Update an employee's role in the database."""
    conn = sqlite3.connect("personal_data.db")
    cursor = conn.cursor()
    cursor.execute('UPDATE employees SET role = ? WHERE id = ?', (new_role, employee_id))
    conn.commit()
    conn.close()

def update_employee_group(employee_id, new_group):
    """Update an employee's group in the database."""
    conn = sqlite3.connect("personal_data.db")
    cursor = conn.cursor()
    cursor.execute('UPDATE employees SET "group" = ? WHERE id = ?', (new_group, employee_id))
    conn.commit()
    conn.close()


def delete_employee(employee_id):
    """Delete an employee from the database."""
    conn = sqlite3.connect("personal_data.db")
    cursor = conn.cursor()
    cursor.execute('DELETE FROM employees WHERE id = ?', (employee_id,))
    conn.commit()
    conn.close()