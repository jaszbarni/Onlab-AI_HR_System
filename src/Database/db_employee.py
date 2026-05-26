
from Database.db_database_manager import db_connection
import classes.user_class as User

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

def update_employee_email(employee_id, new_email):
    """Update an employee's email in the database."""
    try:
        with db_connection() as cursor:
            cursor.execute('UPDATE employees SET email = ? WHERE id = ?', (new_email, employee_id))
        return True
    except Exception as e:
        print(f"Error updating employee email: {e}")
        return False

def update_employee_email_password(employee_id, new_password):
    """Update an employee's email password in the database."""
    try:
        with db_connection() as cursor:
            cursor.execute('UPDATE employees SET email_password = ? WHERE id = ?', (new_password, employee_id))
        return True
    except Exception as e:
        print(f"Error updating employee email password: {e}")
        return False

def get_user_by_email(email):
    """Retrieve a user by their email address."""
    with db_connection() as cursor:
        cursor.execute('SELECT id, first_name, last_name, email, position, password_hash, email_password FROM employees WHERE email = ?', (email.lower(),))
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "first_name": row[1],
                "last_name": row[2],
                "email": row[3],
                "position": row[4],
                "password_hash": row[5],
                "email_password": row[6]
            }
        return None
