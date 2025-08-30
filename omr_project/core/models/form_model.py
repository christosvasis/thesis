from typing import List, Dict, Any
from dataclasses import dataclass, field, asdict
from core.models.question_model import Question


@dataclass(slots=True)
class Form:
    """
    Represents a complete OMR form containing multiple questions.
    
    This class manages the overall structure of an OMR test form, including
    metadata (title, instructions) and the collection of questions. It provides
    validation functionality to ensure form integrity before PDF generation
    and serialization methods for saving/loading forms.

    Attributes:
        title (str): Form title displayed on generated PDF headers
        instructions (str): Instructions shown to students at top of form
        questions (List[Question]): Ordered list of Question objects
    """

    title: str = "New Form"
    instructions: str = "Select the best answer for each question."
    questions: List[Question] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert form to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Form':
        """
        Create form from dictionary data (deserialization).
        
        Args:
            data (dict): Dictionary containing form data
            
        Returns:
            Form: New Form instance with loaded data
        """
        return cls(
            title=data.get('title', 'New Form'),
            instructions=data.get('instructions', 'Select the best answer for each question.'),
            questions=[Question.from_dict(q) for q in data.get('questions', [])],
        )

    def validate(self) -> List[str]:
        """
        Validate form data and return list of errors.
        
        Performs comprehensive validation of the form including metadata
        and all contained questions. Aggregates errors from all questions
        and checks form-level requirements.
        
        Returns:
            List[str]: List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check form metadata
        if not self.title.strip():
            errors.append("Form title is required")
        if not self.questions:
            errors.append("Form must have at least one question")
        
        # Validate each question and include question number in error messages
        for i, q in enumerate(self.questions):
            for error in q.validate():
                errors.append(f"Question {i+1}: {error}")
                
        return errors

    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of form validation status.
        
        Provides a structured summary of validation results that can be
        used to display validation status to users and determine if the
        form is ready for use.
        
        Returns:
            dict: Validation summary with status, message, and error list
        """
        errors = self.validate()
        
        # Return success status if no errors found
        if not errors:
            return {"status": "valid", "message": "Form is ready", "errors": []}

        # Determine if errors are critical (prevent form use) or just warnings
        critical_keywords = ["required", "empty", "at least", "must have"]
        has_critical = any(any(k in e.lower() for k in critical_keywords) for e in errors)

        return {
            "status": "invalid" if has_critical else "warning",
            "message": f"{len(errors)} issue(s) found",
            "errors": errors
        }
