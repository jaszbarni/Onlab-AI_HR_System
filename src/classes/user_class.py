

class User:
    def __init__(self, first_name, last_name, email, role=None, group=None):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.role = role
        self.group = group

    def __str__(self):
        group_str = f", {self.group} group" if self.group else ""
        return f"{self.first_name} {self.last_name} ({self.role}){group_str}, email: {self.email}"
    
