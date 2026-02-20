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
    """Ellenőrzi, hogy a jelenlegi felhasználónak van-e joga az adott művelethez."""
    user_role = st.session_state.user.get("role")
    if user_role in ROLES:
        return permission in ROLES[user_role]
    return False

def init_db():
    conn = sqlite3.connect("personal_data.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT NOT NULL,
                role TEXT NOT NULL,
                "group" TEXT NOT NULL)""")
    conn.commit()
    conn.close()

init_db()

def add_employee(user: User):
    conn = sqlite3.connect("personal_data.db")
    cursor = conn.cursor()
    cursor.execute('INSERT INTO employees (first_name, last_name, email, role, "group") VALUES (?, ?, ?, ?, ?)', #sql injection?
                   (
                       user.first_name,
                       user.last_name,
                       user.email,
                       user.role,
                       user.group
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
            "ID": row[0],
            "First Name": row[1],
            "Last Name": row[2],
            "Email": row[3],
            "Role": row[4],
            "Group": row[5]
        })
        
    return employees
