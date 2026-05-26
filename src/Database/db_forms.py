import streamlit as st
from Database.db_database_manager import db_connection


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

@st.cache_data(ttl=300)
def get_all_form_templates():
    """Get all form templates."""
    with db_connection() as cursor:
        cursor.execute('SELECT id, name, description, created_by, created_date FROM forms WHERE is_template = TRUE ORDER BY created_date DESC')
        forms = cursor.fetchall()
        return forms

@st.cache_data(ttl=300)
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


@st.cache_data(ttl=300)
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

@st.cache_data(ttl=300)
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

@st.cache_data(ttl=3600)
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

@st.cache_data(ttl=3600)
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
