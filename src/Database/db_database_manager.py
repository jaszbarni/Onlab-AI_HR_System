import streamlit as st
import sqlite3
import os
from contextlib import contextmanager

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(CURRENT_DIR, "data.db")
DB_PATH = os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH)

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
    """Check if the current user has a specific permission."""
    if "user" not in st.session_state:
        return False
    
    # Safely get user position with fallback
    user = st.session_state.user
    user_position = getattr(user, 'position', None)
    
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
            
            # Add password_hash column for password-based authentication
            if "password_hash" not in columns:
                cursor.execute("ALTER TABLE employees ADD COLUMN password_hash TEXT")
                
            # Add email_password column for sending emails
            if "email_password" not in columns:
                cursor.execute("ALTER TABLE employees ADD COLUMN email_password TEXT")

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