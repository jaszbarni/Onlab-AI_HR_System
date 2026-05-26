from Database.db_database_manager import db_connection
import classes.user_class as User
import uuid

def generate_user_token(employee_id):
    """Generate and save a new login token for an employee."""
    token = str(uuid.uuid4())
    with db_connection() as cursor:
        cursor.execute('UPDATE employees SET login_token = ? WHERE id = ?', (token, employee_id))
    return token

def set_employee_password(employee_id: int, password: str) -> bool:
    """Set or update password for an employee."""
    try:
        # Storing password in plain text. The 'password_hash' column will contain the plain text password.
        with db_connection() as cursor:
            cursor.execute('UPDATE employees SET password_hash = ? WHERE id = ?', (password, employee_id))
        return True
    except Exception as e:
        print(f"Error setting password: {e}")
        return False

def authenticate_employee(email: str, password: str):
    """Authenticate an employee with email and password."""
    email = email.lower()
    with db_connection() as cursor:
        cursor.execute(
            'SELECT id, first_name, last_name, email, position, password_hash FROM employees WHERE email = ?',
            (email,)
        )
        row = cursor.fetchone()
        
        # The password_hash column now stores plain text passwords.
        if row and row[5]:  # Check if a password exists
            if password == row[5]:
                return User.User(row[1], row[2], row[3], row[4])  # Return User object
        
    return None

def get_user_by_token(token):
    """Retrieve a user by their login token."""
    with db_connection() as cursor:
        cursor.execute('SELECT first_name, last_name, email, position FROM employees WHERE login_token = ?', (token,))
        row = cursor.fetchone()
        if row:
            return User.User(row[0], row[1], row[2], row[3])
        return None
    
def is_employee_registered(email: str) -> bool:
    """Check if an employee exists in the system."""
    email = email.lower()
    with db_connection() as cursor:
        cursor.execute('SELECT id FROM employees WHERE email = ?', (email,))
        return cursor.fetchone() is not None

def has_employee_password(email: str) -> bool:
    """Check if an employee has a password set (is already registered with password)."""
    email = email.lower()
    with db_connection() as cursor:
        cursor.execute('SELECT password_hash FROM employees WHERE email = ?', (email,))
        row = cursor.fetchone()
        return row is not None and row[0] is not None