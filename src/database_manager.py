import streamlit as st
import sqlite3
import classes.user_class as User
import os

# Define the database path using an environment variable, with a fallback for local development
DB_PATH = os.environ.get("DATABASE_PATH", "data.db")

# --- User Management & Permissions ---
# Role definíciók és a hozzájuk tartozó jogosultságok (CRUD)
ROLES = {
    "Vezető": ["create", "read", "update", "delete"],
    "Manager": ["create", "read", "update"],
    "Back office": ["read"],
    "Fizikai": []
}

def get_all_roles():
    return list(ROLES.keys())



def check_permission(permission):
    user_role = st.session_state.user.role
    if user_role in ROLES:
        return permission in ROLES[user_role]
    else:
        st.error("Invalid user role.")
        return False
    

# --- Database Management ---

def init_db():
    # Ensure the directory for the database file exists, only if a path is specified
    dir_name = os.path.dirname(DB_PATH)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Create employees table
    cursor.execute("""CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT NOT NULL,
                role TEXT)""")
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
    # Create campaigns table
    cursor.execute("""CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_by TEXT NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    # Create forms table
    cursor.execute("""CREATE TABLE IF NOT EXISTS forms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                campaign_id INTEGER,
                created_by TEXT NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE)""")
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
    # Create form responses table
    cursor.execute("""CREATE TABLE IF NOT EXISTS form_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                form_id INTEGER NOT NULL,
                submitted_by TEXT NOT NULL,
                submitted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (form_id) REFERENCES forms(id) ON DELETE CASCADE)""")
    # Create response answers table
    cursor.execute("""CREATE TABLE IF NOT EXISTS response_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                answer TEXT NOT NULL,
                FOREIGN KEY (response_id) REFERENCES form_responses(id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE)""")
    # Create form_assignments table
    cursor.execute("""CREATE TABLE IF NOT EXISTS form_assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        form_id INTEGER NOT NULL,
        filler_employee_id INTEGER NOT NULL,
        target_employee_id INTEGER NOT NULL,
        form_type TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        FOREIGN KEY (form_id) REFERENCES forms(id) ON DELETE CASCADE,
        FOREIGN KEY (filler_employee_id) REFERENCES employees(id) ON DELETE CASCADE,
        FOREIGN KEY (target_employee_id) REFERENCES employees(id) ON DELETE CASCADE
    )""")
    conn.commit()
    conn.close()

def migrate_db():
    """Apply database migrations."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if campaign_id column exists in forms table
        cursor.execute("PRAGMA table_info(forms)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "campaign_id" not in columns:
            # Add campaign_id column if it doesn't exist
            cursor.execute("ALTER TABLE forms ADD COLUMN campaign_id INTEGER DEFAULT NULL")
            conn.commit()
        
        if "assigned_group" not in columns:
            # Add assigned_group column if it doesn't exist
            cursor.execute("ALTER TABLE forms ADD COLUMN assigned_group TEXT DEFAULT NULL")
            conn.commit()
            
        # Check if form_type column exists in form_assignments table
        cursor.execute("PRAGMA table_info(form_assignments)")
        columns = [column[1] for column in cursor.fetchall()]
        if "form_type" not in columns:
            cursor.execute("ALTER TABLE form_assignments ADD COLUMN form_type TEXT")
            conn.commit()
    except Exception as e:
        # If migration fails, silently continue
        try:
            conn.rollback()
        except:
            pass
    finally:
        conn.close()

init_db()
migrate_db()

def add_employee(user: User):
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT name FROM groups ORDER BY name')
    groups = [g[0] for g in cursor.fetchall()]
    conn.close()
    return groups

def add_group_to_employee(employee_id, group_name):
    """Add a group to an employee."""
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM employee_groups
                     WHERE employee_id = ? AND group_id = (
                         SELECT id FROM groups WHERE name = ?
                     )''', (employee_id, group_name))
    conn.commit()
    conn.close()

def add_group(group_name):
    """Add a new group to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO groups (name) VALUES (?)', (group_name,))
    conn.commit()
    conn.close()


def delete_group(group_name):
    """Delete a group from the database."""
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE employees SET role = ? WHERE id = ?', (new_role, employee_id))
    conn.commit()
    conn.close()

def delete_employee(employee_id):
    """Delete an employee from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Delete from employee_groups first (foreign key constraint)
    cursor.execute('DELETE FROM employee_groups WHERE employee_id = ?', (employee_id,))
    # Delete from employees
    cursor.execute('DELETE FROM employees WHERE id = ?', (employee_id,))
    conn.commit()
    conn.close()


# --- Campaign Management ---

def create_campaign(name, description, created_by):
    """Create a new campaign."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO campaigns (name, description, created_by) VALUES (?, ?, ?)',
                   (name, description, created_by))
    campaign_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return campaign_id

def get_all_campaigns():
    """Get all campaigns."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, description, created_by, created_date FROM campaigns ORDER BY created_date DESC')
    campaigns = cursor.fetchall()
    conn.close()
    return campaigns

def get_campaign_by_id(campaign_id):
    """Get a specific campaign by ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, description FROM campaigns WHERE id = ?', (campaign_id,))
    campaign = cursor.fetchone()
    conn.close()
    return campaign

def update_campaign(campaign_id, name, description):
    """Update a campaign's name and description."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE campaigns SET name = ?, description = ? WHERE id = ?', (name, description, campaign_id))
    conn.commit()
    conn.close()

def delete_campaign(campaign_id):
    """Delete a campaign and all its forms."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Forms and their questions will be deleted automatically due to CASCADE
    cursor.execute('DELETE FROM campaigns WHERE id = ?', (campaign_id,))
    conn.commit()
    conn.close()

# --- Form Management ---

def create_form(name, description, created_by, campaign_id=None):
    """Create a new form."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO forms (name, description, created_by, campaign_id) VALUES (?, ?, ?, ?)',
                   (name, description, created_by, campaign_id))
    form_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return form_id

def get_all_forms():
    """Get all forms."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, description, created_by, created_date FROM forms ORDER BY created_date DESC')
    forms = cursor.fetchall()
    conn.close()
    return forms

def get_forms_for_user_by_email(email):
    """Get all forms assigned to a specific user by their email."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # First, get the employee ID from email
    cursor.execute('SELECT id FROM employees WHERE email = ?', (email,))
    employee_row = cursor.fetchone()
    
    if not employee_row:
        conn.close()
        return []
        
    employee_id = employee_row[0]
    
    # Then, get the forms assigned to this employee
    cursor.execute("""
        SELECT DISTINCT f.id, f.name, f.description, f.created_by, f.created_date
        FROM forms f
        JOIN form_assignments fa ON f.id = fa.form_id
        WHERE fa.filler_employee_id = ?
    """, (employee_id,))
    
    forms = cursor.fetchall()
    conn.close()
    return forms


def get_forms_by_campaign(campaign_id):
    """Get all forms for a specific campaign."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, description, created_by, created_date FROM forms WHERE campaign_id = ? ORDER BY created_date DESC', (campaign_id,))
    forms = cursor.fetchall()
    conn.close()
    return forms

def get_form_by_id(form_id):
    """Get a specific form by ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, description, created_by, created_date FROM forms WHERE id = ?', (form_id,))
    form = cursor.fetchone()
    conn.close()
    return form

def update_form(form_id, name, description):
    """Update a form's name and description."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE forms SET name = ?, description = ? WHERE id = ?', (name, description, form_id))
    conn.commit()
    conn.close()

def delete_form(form_id):
    """Delete a form and all its questions."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Questions will be deleted automatically due to CASCADE
    cursor.execute('DELETE FROM forms WHERE id = ?', (form_id,))
    conn.commit()
    conn.close()

def assign_group_to_campaign(campaign_id, group_name):
    """Assign a group to a form."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE forms SET assigned_group = ? WHERE id = ?', (group_name, campaign_id))
    conn.commit()
    conn.close()

def get_assigned_group(form_id):
    """Get the assigned group for a form."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT assigned_group FROM forms WHERE id = ?', (form_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def add_question(form_id, question_text, question_type, min_value=None, max_value=None):
    """Add a question to a form."""
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, question_text, question_type, min_value, max_value, question_order FROM questions WHERE form_id = ? ORDER BY question_order', (form_id,))
    questions = cursor.fetchall()
    conn.close()
    return questions

def update_question(question_id, question_text, question_type, min_value=None, max_value=None):
    """Update a question."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE questions SET question_text = ?, question_type = ?, min_value = ?, max_value = ? WHERE id = ?',
                   (question_text, question_type, min_value, max_value, question_id))
    conn.commit()
    conn.close()

def delete_question(question_id):
    """Delete a question."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM questions WHERE id = ?', (question_id,))
    conn.commit()
    conn.close()

def reorder_questions(form_id, question_orders):
    """Update the order of questions. question_orders is a list of (question_id, new_order) tuples."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for question_id, order in question_orders:
        cursor.execute('UPDATE questions SET question_order = ? WHERE id = ?', (order, question_id))
    conn.commit()
    conn.close()

# --- Form Response Management ---

def submit_form_response(form_id, answers_dict, submitted_by):
    """Submit a form response with answers. answers_dict is {question_id: answer}."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create a new response record
    cursor.execute('INSERT INTO form_responses (form_id, submitted_by) VALUES (?, ?)',
                   (form_id, submitted_by))
    response_id = cursor.lastrowid
    
    # Insert all answers
    for question_id, answer in answers_dict.items():
        cursor.execute('INSERT INTO response_answers (response_id, question_id, answer) VALUES (?, ?, ?)',
                       (response_id, question_id, str(answer)))
    
    conn.commit()
    conn.close()
    return response_id

def get_form_responses(form_id):
    """Get all responses for a form."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, submitted_by, submitted_date FROM form_responses WHERE form_id = ? ORDER BY submitted_date DESC',
                   (form_id,))
    responses = cursor.fetchall()
    conn.close()
    return responses

def get_response_answers(response_id):
    """Get all answers for a specific response."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''SELECT ra.question_id, q.question_text, q.question_type, ra.answer 
                      FROM response_answers ra
                      JOIN questions q ON ra.question_id = q.id
                      WHERE ra.response_id = ?
                      ORDER BY q.question_order''', (response_id,))
    answers = cursor.fetchall()
    conn.close()
    return answers


def add_form_assignments(form_id, assignments):
    """Add form evaluation assignments to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all employees to create a name -> id mapping
    cursor.execute("SELECT id, first_name, last_name FROM employees")
    all_employees = cursor.fetchall()
    employee_map = {f"{first} {last}": emp_id for emp_id, first, last in all_employees}

    for assignment in assignments:
        filler_name = assignment["form_filler"]
        target_name = assignment["target"]
        form_type = assignment.get("form_type")

        filler_id = employee_map.get(filler_name)
        target_id = employee_map.get(target_name)

        if filler_id and target_id:
            cursor.execute("""
                INSERT INTO form_assignments (form_id, filler_employee_id, target_employee_id, form_type)
                VALUES (?, ?, ?, ?)
            """, (form_id, filler_id, target_id, form_type))

    conn.commit()
    conn.close()
