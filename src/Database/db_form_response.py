from Database.db_database_manager import db_connection
from datetime import datetime

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

def get_employee_evaluation_for_campaign(employee_id, campaign_id):
    """Get all submitted form responses and answers for a specific campaign for a specific employee."""
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
            WHERE fa.target_employee_id = ? AND f.campaign_id = ? AND fa.status = 'completed'
        """, (employee_id, campaign_id))
        
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