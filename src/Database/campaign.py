from Database.database_manager import db_connection


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

def assign_group_to_campaign(campaign_id, group_name):
    """Assign a group to a campaign."""
    with db_connection() as cursor:
        cursor.execute('UPDATE forms SET assigned_group = ? WHERE id = ?', (group_name, campaign_id))
