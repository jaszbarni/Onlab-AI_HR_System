import streamlit as st
import sqlite3
import classes.user_class as User
import os
import functools
from contextlib import contextmanager
import uuid
from datetime import datetime

# Define the database path using an environment variable, with a fallback for local development
DB_PATH = os.environ.get("DATABASE_PATH", "data.db")

@contextmanager
def db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn.cursor()
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# Define the database path using an environment variable, with a fallback for local development
DB_PATH = os.environ.get("DATABASE_PATH", "data.db")

# --- User Management & Permissions ---
# Position definíciók és a hozzájuk tartozó jogosultságok (CRUD)
POSITIONS = {
    "Vezető": ["create", "read", "update", "delete"],
    "Manager": ["create", "read", "update"],
    "Back office": ["read"],
    "Fizikai": []
}

def get_all_positions():
    """Get all available positions from the database."""
    with db_connection() as cursor:
        cursor.execute('SELECT name FROM positions ORDER BY name')
        positions = [r[0] for r in cursor.fetchall()]
        return positions

def get_all_positions_with_permissions():
    """Get all available positions and their permissions from the database."""
    with db_connection() as cursor:
        cursor.execute('SELECT name, permissions FROM positions ORDER BY name')
        positions = []
        for row in cursor.fetchall():
            permissions = row[1].split(',') if row[1] else []
            permissions = [p.strip() for p in permissions if p.strip()]
            positions.append({"name": row[0], "permissions": permissions})
        return positions

def check_permission(permission):
    if "user" not in st.session_state:
        return False
    user_position = st.session_state.user.position
    if not user_position:
        return False
    with db_connection() as cursor:
        cursor.execute('SELECT permissions FROM positions WHERE name = ?', (user_position,))
        result = cursor.fetchone()
        if result:
            permissions = result[0].split(',') if result[0] else []
            return permission in permissions
        else:
            return False
    

# --- Database Management ---

def init_db():
    # Ensure the directory for the database file exists, only if a path is specified
    dir_name = os.path.dirname(DB_PATH)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with db_connection() as cursor:
        # Create employees table
        cursor.execute("""CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    position TEXT,
                    login_token TEXT UNIQUE,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    position_acquired_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        # Create groups table
        cursor.execute("""CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE)""")
        # Create positions table
        cursor.execute("""CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    permissions TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
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
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT NOT NULL DEFAULT 'open')""")
        # Create forms table
        cursor.execute("""CREATE TABLE IF NOT EXISTS forms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    campaign_id INTEGER,
                    created_by TEXT NOT NULL,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_template BOOLEAN NOT NULL DEFAULT 1,
                    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE)""")
        # Create questions table
        cursor.execute("""CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    form_id INTEGER NOT NULL,
                    question_text TEXT NOT NULL,
                    question_description TEXT,
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
        # Create ai_reviews table
        cursor.execute("""CREATE TABLE IF NOT EXISTS ai_reviews (
            employee_id INTEGER PRIMARY KEY,
            review_text TEXT NOT NULL,
            eval_hash TEXT NOT NULL,
            eval_date TEXT,
            generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
        )""")

def migrate_db():
    """Apply database migrations."""
    try:
        with db_connection() as cursor:
            # Migration: Rename 'roles' table to 'positions'
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='roles'")
            if cursor.fetchone():
                try:
                    cursor.execute("ALTER TABLE roles RENAME TO positions")
                except sqlite3.OperationalError:
                    # RENAME not supported, skip (or handle complex migration)
                    pass

            # Check if positions table is empty, if so, populate it
            cursor.execute("SELECT COUNT(*) FROM positions")
            if cursor.fetchone()[0] == 0:
                POSITIONS = {
                    "Vezető": ["create", "read", "update", "delete"],
                    "Manager": ["create", "read", "update"],
                    "Back office": ["read"],
                    "Fizikai": []
                }
                for position, permissions in POSITIONS.items():
                    cursor.execute("INSERT INTO positions (name, permissions) VALUES (?, ?)", (position, ",".join(permissions)))

            # Check if campaign_id column exists in forms table
            cursor.execute("PRAGMA table_info(forms)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if "campaign_id" not in columns:
                # Add campaign_id column if it doesn't exist
                cursor.execute("ALTER TABLE forms ADD COLUMN campaign_id INTEGER DEFAULT NULL")
            
            if "assigned_group" not in columns:
                # Add assigned_group column if it doesn't exist
                cursor.execute("ALTER TABLE forms ADD COLUMN assigned_group TEXT DEFAULT NULL")
                
            # Check if form_type column exists in form_assignments table
            cursor.execute("PRAGMA table_info(form_assignments)")
            columns = [column[1] for column in cursor.fetchall()]
            if "form_type" not in columns:
                cursor.execute("ALTER TABLE form_assignments ADD COLUMN form_type TEXT")
            
            # Check if status column exists in campaigns table
            cursor.execute("PRAGMA table_info(campaigns)")
            columns = [column[1] for column in cursor.fetchall()]
            if "status" not in columns:
                cursor.execute("ALTER TABLE campaigns ADD COLUMN status TEXT NOT NULL DEFAULT 'open'")

            # Check if is_template column exists in forms table
            cursor.execute("PRAGMA table_info(forms)")
            columns = [column[1] for column in cursor.fetchall()]
            if "is_template" not in columns:
                cursor.execute("ALTER TABLE forms ADD COLUMN is_template BOOLEAN NOT NULL DEFAULT 1")

            # Ensure a Self-evaluation template always exists
            cursor.execute("SELECT COUNT(*) FROM forms WHERE name = 'Self-evaluation' AND is_template = 1")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO forms (name, description, created_by, is_template) VALUES (?, ?, ?, ?)",
                               ('Self-evaluation', 'Default template for self-evaluations', 'System', 1))
                               
            # Check if question_description column exists in questions table
            cursor.execute("PRAGMA table_info(questions)")
            columns = [column[1] for column in cursor.fetchall()]
            if "question_description" not in columns:
                cursor.execute("ALTER TABLE questions ADD COLUMN question_description TEXT")

            # Check if login_token column exists in employees table
            cursor.execute("PRAGMA table_info(employees)")
            columns = [column[1] for column in cursor.fetchall()]
            if "login_token" not in columns:
                cursor.execute("ALTER TABLE employees ADD COLUMN login_token TEXT")
                cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_employees_login_token ON employees(login_token)")
            
            # Migration: Rename 'role' column to 'position'
            if "role" in columns and "position" not in columns:
                cursor.execute("ALTER TABLE employees RENAME COLUMN role TO position")
            
            # Migration: Rename 'role_acquired_date' column to 'position_acquired_date'
            if "role_acquired_date" in columns and "position_acquired_date" not in columns:
                cursor.execute("ALTER TABLE employees RENAME COLUMN role_acquired_date TO position_acquired_date")

            if "created_date" not in columns:
                cursor.execute("ALTER TABLE employees ADD COLUMN created_date TIMESTAMP")
                
            if "position_acquired_date" not in columns:
                cursor.execute("ALTER TABLE employees ADD COLUMN position_acquired_date TIMESTAMP")
                cursor.execute("UPDATE employees SET position_acquired_date = created_date WHERE position_acquired_date IS NULL")
                
            # Check if created_date column exists in positions table
            cursor.execute("PRAGMA table_info(positions)")
            columns = [column[1] for column in cursor.fetchall()]
            if "created_date" not in columns:
                cursor.execute("ALTER TABLE positions ADD COLUMN created_date TIMESTAMP")

            # Check if ai_reviews table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_reviews'")
            if not cursor.fetchone():
                cursor.execute("""CREATE TABLE ai_reviews (
                    employee_id INTEGER PRIMARY KEY,
                    review_text TEXT NOT NULL,
                    eval_hash TEXT NOT NULL,
                eval_date TEXT,
                    generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE)""")
                
            # Check if eval_date column exists in ai_reviews table
            cursor.execute("PRAGMA table_info(ai_reviews)")
            columns = [column[1] for column in cursor.fetchall()]
            if "eval_date" not in columns:
                cursor.execute("ALTER TABLE ai_reviews ADD COLUMN eval_date TEXT")

    except Exception as e:
        # If migration fails, log the error
        print(f"Migration failed: {e}")

init_db()
migrate_db()

def add_employee(user: User):
    with db_connection() as cursor:
        cursor.execute('INSERT INTO employees (first_name, last_name, email, position) VALUES (?, ?, ?, ?)',
                       (
                           user.first_name,
                           user.last_name,
                           user.email,
                           user.position
                       ))
        employee_id = cursor.lastrowid
        
        # Add the group if provided
        if user.group:
            cursor.execute('INSERT OR IGNORE INTO groups (name) VALUES (?)', (user.group,))
            cursor.execute('SELECT id FROM groups WHERE name = ?', (user.group,))
            group_id = cursor.fetchone()[0]
            cursor.execute('INSERT OR IGNORE INTO employee_groups (employee_id, group_id) VALUES (?, ?)',
                           (employee_id, group_id))

def get_all_employees():
    with db_connection() as cursor:
        cursor.execute('''
            SELECT e.id, e.first_name, e.last_name, e.email, e.position, GROUP_CONCAT(g.name), e.created_date, e.position_acquired_date
            FROM employees e
            LEFT JOIN employee_groups eg ON e.id = eg.employee_id
            LEFT JOIN groups g ON eg.group_id = g.id
            GROUP BY e.id
        ''')
        rows = cursor.fetchall()
        
        employees = []
        for row in rows:
            groups = row[5].split(',') if row[5] else []
            employees.append({
                "id": row[0],
                "first_name": row[1],
                "last_name": row[2],
                "email": row[3],
                "position": row[4],
                "groups": groups,
                "created_date": row[6],
                "position_acquired_date": row[7]
            })
        
        return employees

def get_user_by_token(token):
    """Retrieve a user by their login token."""
    with db_connection() as cursor:
        cursor.execute('SELECT first_name, last_name, email, position FROM employees WHERE login_token = ?', (token,))
        row = cursor.fetchone()
        if row:
            return User.User(row[0], row[1], row[2], row[3])
        return None

def generate_user_token(employee_id):
    """Generate and save a new login token for an employee."""
    token = str(uuid.uuid4())
    with db_connection() as cursor:
        cursor.execute('UPDATE employees SET login_token = ? WHERE id = ?', (token, employee_id))
    return token

def get_all_groups():
    """Get all available groups."""
    with db_connection() as cursor:
        cursor.execute('SELECT DISTINCT name FROM groups ORDER BY name')
        groups = [g[0] for g in cursor.fetchall()]
        return groups

def add_group_to_employee(employee_id, group_name):
    """Add a group to an employee."""
    with db_connection() as cursor:
        # Insert or ignore the group
        cursor.execute('INSERT OR IGNORE INTO groups (name) VALUES (?)', (group_name,))
        # Get the group ID
        cursor.execute('SELECT id FROM groups WHERE name = ?', (group_name,))
        group_id = cursor.fetchone()[0]
        # Add the employee to the group
        cursor.execute('INSERT OR IGNORE INTO employee_groups (employee_id, group_id) VALUES (?, ?)',
                       (employee_id, group_id))

def remove_group_from_employee(employee_id, group_name):
    """Remove a group from an employee."""
    with db_connection() as cursor:
        cursor.execute('''DELETE FROM employee_groups
                         WHERE employee_id = ? AND group_id = (
                             SELECT id FROM groups WHERE name = ?
                         )''', (employee_id, group_name))

def add_group(group_name):
    """Add a new group to the database."""
    with db_connection() as cursor:
        cursor.execute('INSERT INTO groups (name) VALUES (?)', (group_name,))


def delete_group(group_name):
    """Delete a group from the database."""
    with db_connection() as cursor:
        # Delete from employee_groups first (foreign key constraint)
        cursor.execute('''DELETE FROM employee_groups
                         WHERE group_id = (SELECT id FROM groups WHERE name = ?)''', (group_name,))
        # Delete the group
        cursor.execute('DELETE FROM groups WHERE name = ?', (group_name,))


def add_position(position_name, permissions):
    """Add a new position to the database."""
    with db_connection() as cursor:
        cursor.execute('INSERT INTO positions (name, permissions) VALUES (?, ?)', (position_name, ",".join(permissions)))

def delete_position(position_name):
    """Delete a position from the database."""
    with db_connection() as cursor:
        cursor.execute('DELETE FROM positions WHERE name = ?', (position_name,))

def update_position(position_name, permissions):
    """Update a position's permissions in the database."""
    with db_connection() as cursor:
        cursor.execute('UPDATE positions SET permissions = ? WHERE name = ?', (",".join(permissions), position_name))
        
def update_employee_position(employee_id, new_position):
    """Update an employee's position in the database."""
    with db_connection() as cursor:
        cursor.execute('UPDATE employees SET position = ?, position_acquired_date = CURRENT_TIMESTAMP WHERE id = ?', (new_position, employee_id))

def delete_employee(employee_id):
    """Delete an employee from the database."""
    with db_connection() as cursor:
        # Delete from employee_groups first (foreign key constraint)
        cursor.execute('DELETE FROM employee_groups WHERE employee_id = ?', (employee_id,))
        # Delete from employees
        cursor.execute('DELETE FROM employees WHERE id = ?', (employee_id,))

def delete_all_employees():
    """Delete all employees from the database."""
    with db_connection() as cursor:
        cursor.execute('DELETE FROM employee_groups')
        cursor.execute('DELETE FROM employees')


# --- Campaign Management ---

def create_campaign(name, description, created_by):
    """Create a new campaign."""
    with db_connection() as cursor:
        cursor.execute('INSERT INTO campaigns (name, description, created_by) VALUES (?, ?, ?)',
                       (name, description, created_by))
        campaign_id = cursor.lastrowid
        return campaign_id

def get_all_campaigns():
    """Get all campaigns."""
    with db_connection() as cursor:
        cursor.execute('SELECT id, name, description, status FROM campaigns ORDER BY created_date DESC')
        campaigns = cursor.fetchall()
        return campaigns

def get_campaign_by_id(campaign_id):
    """Get a specific campaign by ID."""
    with db_connection() as cursor:
        cursor.execute('SELECT id, name, description, status FROM campaigns WHERE id = ?', (campaign_id,))
        campaign = cursor.fetchone()
        return campaign

def update_campaign(campaign_id, name, description):
    """Update a campaign's name and description."""
    with db_connection() as cursor:
        cursor.execute('UPDATE campaigns SET name = ?, description = ? WHERE id = ?', (name, description, campaign_id))

def update_campaign_status(campaign_id, status):
    """Update a campaign's status."""
    with db_connection() as cursor:
        cursor.execute('UPDATE campaigns SET status = ? WHERE id = ?', (status, campaign_id))

def delete_campaign(campaign_id):
    """Delete a campaign and all its forms."""
    with db_connection() as cursor:
        # Forms and their questions will be deleted automatically due to CASCADE
        cursor.execute('DELETE FROM campaigns WHERE id = ?', (campaign_id,))

# --- Form Management ---

def create_form(name, description, created_by, campaign_id=None, is_template=True):
    """Create a new form."""
    with db_connection() as cursor:
        cursor.execute('INSERT INTO forms (name, description, created_by, campaign_id, is_template) VALUES (?, ?, ?, ?, ?)',
                       (name, description, created_by, campaign_id, is_template))
        form_id = cursor.lastrowid
        return form_id

def create_form_from_template(template_id, campaign_id, created_by):
    """Create a new form from a template for a specific campaign."""
    with db_connection() as cursor:
        # Get template data
        cursor.execute('SELECT name, description FROM forms WHERE id = ?', (template_id,))
        template_data = cursor.fetchone()
        if not template_data:
            raise ValueError("Template not found")
        
        template_name, template_description = template_data
        
        # Create a new form for the campaign
        new_form_id = create_form(
            name=template_name,
            description=template_description,
            created_by=created_by,
            campaign_id=campaign_id,
            is_template=False
        )
        
        # Copy questions from the template to the new form
        questions = get_questions_by_form(template_id)
        for q in questions:
            add_question(
                form_id=new_form_id,
                question_text=q[1],
                question_description=q[2],
                question_type=q[3],
                min_value=q[4],
                max_value=q[5]
            )
        
        return new_form_id

def get_all_form_templates():
    """Get all form templates."""
    with db_connection() as cursor:
        cursor.execute('SELECT id, name, description, created_by, created_date FROM forms WHERE is_template = TRUE ORDER BY created_date DESC')
        forms = cursor.fetchall()
        return forms

def get_all_forms():
    """Get all forms that are not templates."""
    with db_connection() as cursor:
        cursor.execute('SELECT id, name, description, created_by, created_date FROM forms WHERE is_template = FALSE ORDER BY created_date DESC')
        forms = cursor.fetchall()
        return forms

def get_forms_for_user_by_email(email):
    """Get all forms assigned to a specific user by their email."""
    with db_connection() as cursor:
        # First, get the employee ID from email
        cursor.execute('SELECT id FROM employees WHERE email = ?', (email,))
        employee_row = cursor.fetchone()
        
        if not employee_row:
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
        return forms


def get_forms_by_campaign(campaign_id):
    """Get all forms for a specific campaign."""
    with db_connection() as cursor:
        cursor.execute('SELECT id, name, description, created_by, created_date FROM forms WHERE campaign_id = ? ORDER BY created_date DESC', (campaign_id,))
        forms = cursor.fetchall()
        return forms

def get_assignments_for_user_by_email(email):
    """Get all form assignments for a specific user by their email, including the target employee name."""
    with db_connection() as cursor:
        # First, get the employee ID from email
        cursor.execute('SELECT id FROM employees WHERE email = ?', (email,))
        employee_row = cursor.fetchone()
        
        if not employee_row:
            return []
            
        employee_id = employee_row[0]
        
        # Then, get the assignments with the target employee's full name
        cursor.execute("""
            SELECT fa.id, f.id, f.name, f.description, 
                   t.first_name || ' ' || t.last_name AS target_name,
                   fa.status,
                   c.status AS campaign_status
            FROM form_assignments fa
            JOIN forms f ON fa.form_id = f.id
            JOIN employees t ON fa.target_employee_id = t.id
            LEFT JOIN campaigns c ON f.campaign_id = c.id
            WHERE fa.filler_employee_id = ?
        """, (employee_id,))
        
        return cursor.fetchall()

def get_assignments_by_form(form_id):
    """Get all form assignments for a specific form, including employee names."""
    with db_connection() as cursor:
        cursor.execute("""
            SELECT fa.id, 
                   f.first_name || ' ' || f.last_name AS filler_name,
                   t.first_name || ' ' || t.last_name AS target_name,
                   fa.status
            FROM form_assignments fa
            JOIN employees f ON fa.filler_employee_id = f.id
            JOIN employees t ON fa.target_employee_id = t.id
            WHERE fa.form_id = ?
        """, (form_id,))
        return cursor.fetchall()

def update_assignment_status(assignment_id, status):
    """Update the status of a form assignment."""
    with db_connection() as cursor:
        cursor.execute('UPDATE form_assignments SET status = ? WHERE id = ?', (status, assignment_id))

def delete_all_assignments():
    """Delete all form assignments from the database."""
    with db_connection() as cursor:
        cursor.execute('DELETE FROM form_assignments')

def get_form_by_id(form_id):
    """Get a specific form by ID."""
    with db_connection() as cursor:
        cursor.execute('SELECT id, name, description, created_by, created_date, campaign_id FROM forms WHERE id = ?', (form_id,))
        form = cursor.fetchone()
        return form

def update_form(form_id, name, description):
    """Update a form's name and description."""
    with db_connection() as cursor:
        cursor.execute('UPDATE forms SET name = ?, description = ? WHERE id = ?', (name, description, form_id))

def delete_form(form_id):
    """Delete a form and all its questions."""
    with db_connection() as cursor:
        # Questions will be deleted automatically due to CASCADE
        cursor.execute('DELETE FROM forms WHERE id = ?', (form_id,))

def delete_all_forms():
    """Delete all forms from the database."""
    with db_connection() as cursor:
        cursor.execute('DELETE FROM forms')

def assign_group_to_campaign(campaign_id, group_name):
    """Assign a group to a campaign."""
    with db_connection() as cursor:
        cursor.execute('UPDATE forms SET assigned_group = ? WHERE id = ?', (group_name, campaign_id))

def add_question(form_id, question_text, question_description, question_type, min_value=None, max_value=None):
    """Add a question to a form."""
    with db_connection() as cursor:
        # Get the max order for this form
        cursor.execute('SELECT MAX(question_order) FROM questions WHERE form_id = ?', (form_id,))
        max_order = cursor.fetchone()[0]
        next_order = (max_order + 1) if max_order is not None else 0
        
        cursor.execute('INSERT INTO questions (form_id, question_text, question_description, question_type, min_value, max_value, question_order) VALUES (?, ?, ?, ?, ?, ?, ?)',
                       (form_id, question_text, question_description, question_type, min_value, max_value, next_order))
        question_id = cursor.lastrowid
        return question_id

def get_questions_by_form(form_id):
    """Get all questions for a form."""
    with db_connection() as cursor:
        cursor.execute('SELECT id, question_text, question_description, question_type, min_value, max_value, question_order FROM questions WHERE form_id = ? ORDER BY question_order', (form_id,))
        questions = cursor.fetchall()
        return questions

def update_question(question_id, question_text, question_description, question_type, min_value=None, max_value=None):
    """Update a question."""
    with db_connection() as cursor:
        cursor.execute('UPDATE questions SET question_text = ?, question_description = ?, question_type = ?, min_value = ?, max_value = ? WHERE id = ?',
                       (question_text, question_description, question_type, min_value, max_value, question_id))

def delete_question(question_id):
    """Delete a question."""
    with db_connection() as cursor:
        cursor.execute('DELETE FROM questions WHERE id = ?', (question_id,))

def reorder_questions(form_id, question_orders):
    """Update the order of questions. question_orders is a list of (question_id, new_order) tuples."""
    with db_connection() as cursor:
        for question_id, order in question_orders:
            cursor.execute('UPDATE questions SET question_order = ? WHERE id = ?', (order, question_id))

# --- Form Response Management ---

def submit_form_response(form_id, answers_dict, submitted_by):
    """Submit a form response with answers. answers_dict is {question_id: answer}."""
    with db_connection() as cursor:
        # Create a new response record
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('INSERT INTO form_responses (form_id, submitted_by, submitted_date) VALUES (?, ?, ?)',
                       (form_id, submitted_by, now))
        response_id = cursor.lastrowid
        
        # Insert all answers
        for question_id, answer in answers_dict.items():
            cursor.execute('INSERT INTO response_answers (response_id, question_id, answer) VALUES (?, ?, ?)',
                           (response_id, question_id, str(answer)))
        
        return response_id

def get_form_responses(form_id):
    """Get all responses for a form."""
    with db_connection() as cursor:
        cursor.execute('SELECT id, submitted_by, submitted_date FROM form_responses WHERE form_id = ? ORDER BY submitted_date DESC',
                       (form_id,))
        responses = cursor.fetchall()
        return responses

def get_response_answers(response_id):
    """Get all answers for a specific response."""
    with db_connection() as cursor:
        cursor.execute('''SELECT ra.question_id, q.question_text, q.question_type, ra.answer 
                          FROM response_answers ra
                          JOIN questions q ON ra.question_id = q.id
                          WHERE ra.response_id = ?
                          ORDER BY q.question_order''', (response_id,))
        answers = cursor.fetchall()
        return answers


def add_form_assignments(assignments):
    """Add form evaluation assignments to the database."""
    with db_connection() as cursor:
        # Get all employees to create a name -> id mapping
        cursor.execute("SELECT id, first_name, last_name FROM employees")
        all_employees = cursor.fetchall()
        employee_map = {f"{first} {last}": emp_id for emp_id, first, last in all_employees}

        for assignment in assignments:
            filler_name = assignment["form_filler"]
            target_name = assignment["target"]
            form_type = assignment.get("form_type")
            form_id = assignment.get("form_id")

            filler_id = employee_map.get(filler_name)
            target_id = employee_map.get(target_name)

            if filler_id and target_id and form_id:
                cursor.execute("""
                    INSERT INTO form_assignments (form_id, filler_employee_id, target_employee_id, form_type)
                    VALUES (?, ?, ?, ?)
                """, (form_id, filler_id, target_id, form_type))

def get_evaluations_for_employee(employee_id):
    """Get all submitted form responses and answers targeting a specific employee."""
    with db_connection() as cursor:
        cursor.execute("SELECT first_name, last_name FROM employees WHERE id = ?", (employee_id,))
        emp = cursor.fetchone()
        if not emp:
            return []

        cursor.execute("""
            SELECT fa.form_id, f.name AS form_name, e.first_name || ' ' || e.last_name AS filler_name
            FROM form_assignments fa
            JOIN forms f ON fa.form_id = f.id
            JOIN employees e ON fa.filler_employee_id = e.id
            WHERE fa.target_employee_id = ? AND fa.status = 'completed'
        """, (employee_id,))
        
        assignments = cursor.fetchall()
        
        evaluations = []
        for form_id, form_name, filler_name in assignments:
            cursor.execute("""
                SELECT id, submitted_date FROM form_responses 
                WHERE form_id = ? AND submitted_by = ?
                ORDER BY submitted_date DESC LIMIT 1
            """, (form_id, filler_name))
            response_row = cursor.fetchone()
            
            if response_row:
                response_id = response_row[0]
                submitted_date = response_row[1]
                cursor.execute("""
                    SELECT q.question_text, q.question_type, ra.answer 
                    FROM response_answers ra
                    JOIN questions q ON ra.question_id = q.id
                    WHERE ra.response_id = ?
                    ORDER BY q.question_order
                """, (response_id,))
                
                answers = cursor.fetchall()
                formatted_answers = [{"question": row[0], "type": row[1], "answer": row[2]} for row in answers]
                
                evaluations.append({
                    "form_name": form_name,
                    "evaluator": filler_name,
                    "submitted_date": submitted_date,
                    "answers": formatted_answers
                })
                
        return evaluations

def get_ai_review(employee_id):
    """Get the saved AI review for an employee."""
    with db_connection() as cursor:
        cursor.execute('SELECT review_text, eval_hash, generated_date, eval_date FROM ai_reviews WHERE employee_id = ?', (employee_id,))
        return cursor.fetchone()

def save_ai_review(employee_id, review_text, eval_hash, eval_date):
    """Save or update an AI review for an employee."""
    with db_connection() as cursor:
        cursor.execute('''INSERT OR REPLACE INTO ai_reviews (employee_id, review_text, eval_hash, eval_date, generated_date) 
                          VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)''', 
                       (employee_id, review_text, eval_hash, eval_date))
        cursor.execute('SELECT generated_date FROM ai_reviews WHERE employee_id = ?', (employee_id,))
        return cursor.fetchone()[0]

def save_company_values(value):
    """Save the single company value text to the database."""
    with db_connection() as cursor:
        cursor.execute('CREATE TABLE IF NOT EXISTS company_values (id INTEGER PRIMARY KEY, value TEXT)')
        # Clear existing values to ensure only one record exists
        cursor.execute('DELETE FROM company_values')
        cursor.execute('INSERT INTO company_values (id, value) VALUES (1, ?)', (value,))

def get_company_values():
    """Get the single company value text from the database."""
    with db_connection() as cursor:
        cursor.execute('CREATE TABLE IF NOT EXISTS company_values (id INTEGER PRIMARY KEY, value TEXT)')
        cursor.execute('SELECT value FROM company_values WHERE id = 1')
        result = cursor.fetchone()
        return result[0] if result else ""