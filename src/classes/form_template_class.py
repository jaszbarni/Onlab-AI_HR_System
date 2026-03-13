import streamlit as st
from database_manager import (
    get_form_by_id, get_questions_by_form, get_response_answers, get_form_responses,
    submit_form_response, get_assigned_group, assign_group_to_campaign
)


class FormTemplate:
    """A class to manage form templates and their responses."""
    
    def __init__(self, form_id):
        """Initialize a form template with its ID."""
        self.form_id = form_id
        self.form_data = None
        self.questions = None
        self.campaign_id = None
        self.load_form()
    
    def load_form(self):
        """Load form data and questions from database."""
        self.form_data = get_form_by_id(self.form_id)
        self.questions = get_questions_by_form(self.form_id)
    
    def get_form_info(self):
        """Return form information tuple (id, name, description, created_by, created_date)."""
        return self.form_data
    
    def get_name(self):
        """Get form name."""
        return self.form_data[1] if self.form_data else None
    
    def get_description(self):
        """Get form description."""
        return self.form_data[2] if self.form_data else None
    
    def get_created_by(self):
        """Get who created the form."""
        return self.form_data[3] if self.form_data else None
    
    def get_questions(self):
        """Get all questions for this form."""
        return self.questions or []
    
    def has_questions(self):
        """Check if form has any questions."""
        return bool(self.questions and len(self.questions) > 0)
    
    def submit_response(self, answers_dict, submitted_by):
        """Submit a form response with answers.
        
        Args:
            answers_dict: Dictionary of {question_id: answer}
            submitted_by: Name of person submitting the form
            
        Returns:
            response_id: ID of the submitted response
        """
        return submit_form_response(self.form_id, answers_dict, submitted_by)
    
    def get_responses(self):
        """Get all responses for this form."""
        return get_form_responses(self.form_id)
    
    def get_response_details(self, response_id):
        """Get detailed answers for a specific response."""
        return get_response_answers(response_id)
    
    def get_question_by_id(self, question_id):
        """Get a specific question by ID."""
        for question in self.questions:
            if question[0] == question_id:
                return question
        return None
    
    def validate_answer(self, question_id, answer):
        """Validate an answer against question constraints.
        
        Args:
            question_id: ID of the question
            answer: The answer to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        question = self.get_question_by_id(question_id)
        if not question:
            return False, "Question not found"
        
        question_id, question_text, question_type, min_val, max_val, order = question
        
        # Allow empty answers for now (can be made optional/required later)
        if answer == "" or answer is None:
            return True, ""
        
        # Validate rating questions
        if question_type in ["0-5 Rating", "1-10 Rating"]:
            try:
                val = int(answer)
                if min_val is not None and val < min_val:
                    return False, f"Value must be at least {min_val}"
                if max_val is not None and val > max_val:
                    return False, f"Value must be at most {max_val}"
            except ValueError:
                return False, "Please enter a valid number"
        
        return True, ""
    
    def has_user_submitted(self, submitted_by):
        """Check if a user has already submitted this form.
        
        Args:
            submitted_by: Name of user (typically "first_name last_name")
            
        Returns:
            Boolean: True if user has already submitted, False otherwise
        """
        responses = self.get_responses()
        return any(response[1] == submitted_by for response in responses)
    
    def get_submitted_users(self):
        """Get list of users who have submitted this form.
        
        Returns:
            List of user names who submitted the form
        """
        responses = self.get_responses()
        return [response[1] for response in responses]    
    def get_assigned_group(self):
        """Get the assigned group for this form."""
        return get_assigned_group(self.form_id)
    
    def assign_group(self, group_name):
        """Assign a group to this form."""
        assign_group_to_campaign(self.campaign_id, group_name)
