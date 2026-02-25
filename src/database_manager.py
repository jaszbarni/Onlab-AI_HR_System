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
    def __init__(self, first_name, last_name, role, email, group=None):
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
        self.group = group
        self.email = email

    def __str__(self):
        group_str = f", {self.group} group" if self.group else ""
        return f"{self.first_name} {self.last_name} ({self.role}){group_str}, email: {self.email}"


def check_permission(permission):
    user_role = st.session_state.user.role
    if user_role in ROLES:
        return permission in ROLES[user_role]
    else:
        st.error("Invalid user role.")
        return False

# --- Database Management ---

def init_db():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    # Create employees table
    cursor.execute("""CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT NOT NULL,
                role TEXT NOT NULL)""")
    # Create groups table
    cursor.execute("""CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE)""")
    # Create employee_groups junction table for many-to-many relationship
    cursor.execute("""CREATE TABLE IF NOT EXISTS employee_groups (
                employee_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                PRIMARY KEY (employee_id, group_id),
                FOREIGN KEY (employee_id) REFERENCES employees(id),
                FOREIGN KEY (group_id) REFERENCES groups(id))""")
    # Create forms table
    cursor.execute("""CREATE TABLE IF NOT EXISTS forms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_by TEXT NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    # Create questions table
    cursor.execute("""CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                form_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                question_type TEXT NOT NULL,
                min_value INTEGER,
                max_value INTEGER,
                question_order INTEGER,
                FOREIGN KEY (form_id) REFERENCES forms(id) ON DELETE CASCADE)""")
    conn.commit()
    conn.close()

init_db()

def add_employee(user: User):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute('INSERT INTO employees (first_name, last_name, email, role) VALUES (?, ?, ?, ?)',
                   (
                       user.first_name,
                       user.last_name,
                       user.email,
                       user.role
                   ))
    employee_id = cursor.lastrowid
    
    # Add the group if provided
    if user.group:
        cursor.execute('INSERT OR IGNORE INTO groups (name) VALUES (?)', (user.group,))
        cursor.execute('SELECT id FROM groups WHERE name = ?', (user.group,))
        group_id = cursor.fetchone()[0]
        cursor.execute('INSERT OR IGNORE INTO employee_groups (employee_id, group_id) VALUES (?, ?)',
                       (employee_id, group_id))
    
    conn.commit()
    conn.close()

def get_all_employees():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM employees')
    rows = cursor.fetchall()
    
    employees = []
    for row in rows:
        employee_id = row[0]
        # Get all groups for this employee
        cursor.execute('''SELECT g.name FROM groups g
                         INNER JOIN employee_groups eg ON g.id = eg.group_id
                         WHERE eg.employee_id = ?''', (employee_id,))
        groups = [g[0] for g in cursor.fetchall()]
        
        employees.append({
            "id": row[0],
            "first_name": row[1],
            "last_name": row[2],
            "email": row[3],
            "groups": groups,
            "role": row[4]
        })
    
    conn.close()
    return employees

def get_all_groups():
    """Get all available groups."""
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT name FROM groups ORDER BY name')
    groups = [g[0] for g in cursor.fetchall()]
    conn.close()
    return groups

def add_group_to_employee(employee_id, group_name):
    """Add a group to an employee."""
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    # Insert or ignore the group
    cursor.execute('INSERT OR IGNORE INTO groups (name) VALUES (?)', (group_name,))
    # Get the group ID
    cursor.execute('SELECT id FROM groups WHERE name = ?', (group_name,))
    group_id = cursor.fetchone()[0]
    # Add the employee to the group
    cursor.execute('INSERT OR IGNORE INTO employee_groups (employee_id, group_id) VALUES (?, ?)',
                   (employee_id, group_id))
    conn.commit()
    conn.close()

def remove_group_from_employee(employee_id, group_name):
    """Remove a group from an employee."""
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM employee_groups
                     WHERE employee_id = ? AND group_id = (
                         SELECT id FROM groups WHERE name = ?
                     )''', (employee_id, group_name))
    conn.commit()
    conn.close()

def add_group(group_name):
    """Add a new group to the database."""
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute('INSERT INTO groups (name) VALUES (?)', (group_name,))
    conn.commit()
    conn.close()


def delete_group(group_name):
    """Delete a group from the database."""
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    # Delete from employee_groups first (foreign key constraint)
    cursor.execute('''DELETE FROM employee_groups
                     WHERE group_id = (SELECT id FROM groups WHERE name = ?)''', (group_name,))
    # Delete the group
    cursor.execute('DELETE FROM groups WHERE name = ?', (group_name,))
    conn.commit()
    conn.close()


def update_employee_role(employee_id, new_role):
    """Update an employee's role in the database."""
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute('UPDATE employees SET role = ? WHERE id = ?', (new_role, employee_id))
    conn.commit()
    conn.close()

def delete_employee(employee_id):
    """Delete an employee from the database."""
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    # Delete from employee_groups first (foreign key constraint)
    cursor.execute('DELETE FROM employee_groups WHERE employee_id = ?', (employee_id,))
    # Delete from employees
    cursor.execute('DELETE FROM employees WHERE id = ?', (employee_id,))
    conn.commit()
    conn.close()


# --- Form Management ---

def create_form(name, description, created_by):
    """Create a new form."""
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute('INSERT INTO forms (name, description, created_by) VALUES (?, ?, ?)',
                   (name, description, created_by))
    form_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return form_id

def get_all_forms():
    """Get all forms."""
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, description, created_by, created_date FROM forms ORDER BY created_date DESC')
    forms = cursor.fetchall()
    conn.close()
    return forms

def get_form_by_id(form_id):
    """Get a specific form by ID."""
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, description, created_by, created_date FROM forms WHERE id = ?', (form_id,))
    form = cursor.fetchone()
    conn.close()
    return form

def update_form(form_id, name, description):
    """Update a form's name and description."""
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute('UPDATE forms SET name = ?, description = ? WHERE id = ?', (name, description, form_id))
    conn.commit()
    conn.close()

def delete_form(form_id):
    """Delete a form and all its questions."""
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    # Questions will be deleted automatically due to CASCADE
    cursor.execute('DELETE FROM forms WHERE id = ?', (form_id,))
    conn.commit()
    conn.close()

def add_question(form_id, question_text, question_type, min_value=None, max_value=None):
    """Add a question to a form."""
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    # Get the max order for this form
    cursor.execute('SELECT MAX(question_order) FROM questions WHERE form_id = ?', (form_id,))
    max_order = cursor.fetchone()[0]
    next_order = (max_order + 1) if max_order is not None else 0
    
    cursor.execute('INSERT INTO questions (form_id, question_text, question_type, min_value, max_value, question_order) VALUES (?, ?, ?, ?, ?, ?)',
                   (form_id, question_text, question_type, min_value, max_value, next_order))
    question_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return question_id

def get_questions_by_form(form_id):
    """Get all questions for a form."""
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute('SELECT id, question_text, question_type, min_value, max_value, question_order FROM questions WHERE form_id = ? ORDER BY question_order', (form_id,))
    questions = cursor.fetchall()
    conn.close()
    return questions

def update_question(question_id, question_text, question_type, min_value=None, max_value=None):
    """Update a question."""
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute('UPDATE questions SET question_text = ?, question_type = ?, min_value = ?, max_value = ? WHERE id = ?',
                   (question_text, question_type, min_value, max_value, question_id))
    conn.commit()
    conn.close()

def delete_question(question_id):
    """Delete a question."""
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute('DELETE FROM questions WHERE id = ?', (question_id,))
    conn.commit()
    conn.close()

def reorder_questions(form_id, question_orders):
    """Update the order of questions. question_orders is a list of (question_id, new_order) tuples."""
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    for question_id, order in question_orders:
        cursor.execute('UPDATE questions SET question_order = ? WHERE id = ?', (order, question_id))
    conn.commit()
    conn.close()