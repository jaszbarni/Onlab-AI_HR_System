
from Database.campaign import delete_campaign, get_campaign_by_id, update_campaign
from Database.forms import create_form, delete_form, get_forms_by_campaign


class Campaign:
    """A class to manage campaigns and their forms."""
    
    def __init__(self, campaign_id):
        """Initialize a campaign with its ID."""
        self.campaign_id = campaign_id
        self.campaign_data = None
        self.forms = None
        self.load_campaign()
    
    def load_campaign(self):
        """Load campaign data and forms from database."""
        self.campaign_data = get_campaign_by_id(self.campaign_id)
        self.forms = get_forms_by_campaign(self.campaign_id)
    
    def get_campaign_info(self):
        """Return campaign information tuple (id, name, description, created_by, created_date)."""
        return self.campaign_data
    
    def get_name(self):
        """Get campaign name."""
        return self.campaign_data[1] if self.campaign_data else None
    
    def get_description(self):
        """Get campaign description."""
        return self.campaign_data[2] if self.campaign_data else None
    
    def get_created_by(self):
        """Get who created the campaign."""
        return self.campaign_data[3] if self.campaign_data else None
    
    def get_forms(self):
        """Get all forms in this campaign."""
        return self.forms or []
    
    def get_form_count(self):
        """Get the number of forms in this campaign."""
        return len(self.forms) if self.forms else 0
    
    def has_forms(self):
        """Check if campaign has any forms."""
        return bool(self.forms and len(self.forms) > 0)
    
    def add_form(self, name, description, created_by):
        """Create a new form in this campaign.
        
        Args:
            name: Form name
            description: Form description
            created_by: User who created the form
            
        Returns:
            form_id: ID of the newly created form
        """
        form_id = create_form(name, description, created_by, self.campaign_id)
        self.load_campaign()  # Refresh forms list
        return form_id
    
    def delete_form(self, form_id):
        """Delete a form from this campaign.
        
        Args:
            form_id: ID of the form to delete
        """
        delete_form(form_id)
        self.load_campaign()  # Refresh forms list
    
    def update_campaign(self, name, description):
        """Update campaign details.
        
        Args:
            name: New campaign name
            description: New campaign description
        """
        update_campaign(self.campaign_id, name, description)
        self.load_campaign()  # Refresh data
    
    def delete_campaign(self):
        """Delete this campaign and all its forms."""
        delete_campaign(self.campaign_id)