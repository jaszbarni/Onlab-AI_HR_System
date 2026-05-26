from Database.db_database_manager import db_connection

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
