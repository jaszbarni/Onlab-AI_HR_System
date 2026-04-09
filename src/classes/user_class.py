

class User:
    def __init__(self, first_name, last_name, email, position, group=None):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.position = position
        self.group = group

    def __str__(self):
        group_str = f", {self.group} group" if self.group else ""
        return f"{self.first_name} {self.last_name} ({self.position}){group_str}, email: {self.email}"
    
